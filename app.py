from flask import Flask, jsonify, request
import imaplib
import email
from email.header import decode_header
from datetime import datetime
import os
from openai import OpenAI
from flask_cors import CORS
from dotenv import load_dotenv
from pymongo import MongoClient
from bson import ObjectId
import requests

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:3000"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})
load_dotenv()

# Print environment variables for debugging
print("Environment variables:")
print(f"GMAIL_EMAIL: {os.getenv('GMAIL_EMAIL')}")
print(f"GMAIL_APP_PASSWORD: {'Set' if os.getenv('GMAIL_APP_PASSWORD') else 'Not set'}")
print(f"AZURE_API_KEY: {'Set' if os.getenv('AZURE_API_KEY') else 'Not set'}")
print(f"AZURE_ENDPOINT: {'Set' if os.getenv('AZURE_ENDPOINT') else 'Not set'}")

# Email credentials from environment variables
EMAIL = os.getenv('GMAIL_EMAIL')
PASSWORD = os.getenv('GMAIL_APP_PASSWORD')
IMAP_SERVER = "imap.gmail.com"

# Azure OpenAI setup
AZURE_API_KEY = os.getenv('AZURE_API_KEY')
AZURE_ENDPOINT = os.getenv('AZURE_ENDPOINT')
AZURE_DEPLOYMENT_NAME = os.getenv('AZURE_DEPLOYMENT_NAME')
AZURE_API_VERSION = os.getenv('AZURE_API_VERSION')

# OpenAI client setup
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv('OPENROUTER_API_KEY'),
    default_headers={  # Required headers for OpenRouter
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "Email Summary Service"
    }
)

# MongoDB setup
MONGO_URI = "mongodb://localhost:27017"
mongo_client = MongoClient(MONGO_URI)
db = mongo_client.email_dashboard
emails_collection = db.emails
attachments_collection = db.pdf_attachments
schedules_collection = db.schedules
spam_emails_collection = db.spam_emails

@app.route('/api/emails')
def get_emails():
    try:
        # Get last 2 emails from MongoDB
        emails = list(emails_collection.find(
            {},
            {'summary': 1, 'date': 1, 'subject': 1, '_id': 0}
        ).sort('email_id', -1).limit(2))
        
        return jsonify({
            "summaries": [email['summary'] for email in emails]
        })
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/stored-emails')
def get_stored_emails():
    try:
        stored_emails = list(emails_collection.find(
            {},
            {
                'subject': 1,
                'sender': 1,
                'date': 1,
                'body': 1,
                'summary': 1,
                'processed_at': 1,
                'has_attachments': 1,
                'pdf_attachments': 1,
                'category': 1,
                'isRead': 1,
                'isStarred': 1,
                'labels': 1,
                '_id': 1
            }
        ).sort('processed_at', -1))
        
        # Add debug logging
        print(f"Found {len(stored_emails)} emails")
        
        # Format emails for frontend
        formatted_emails = []
        for email in stored_emails:
            try:
                # Convert MongoDB ObjectId to string
                email_id = str(email['_id'])
                
                # Ensure processed_at is string
                processed_at = email.get('processed_at', '')
                if isinstance(processed_at, datetime):
                    processed_at = processed_at.isoformat()
                
                formatted_email = {
                    'id': email_id,
                    'subject': email.get('subject', 'No Subject'),
                    'sender': email.get('sender', 'Unknown Sender'),
                    'date': email.get('date', ''),
                    'body': email.get('body', ''),
                    'summary': email.get('summary', ''),
                    'category': email.get('category', 'primary'),
                    'isRead': email.get('isRead', False),
                    'isStarred': email.get('isStarred', False),
                    'labels': email.get('labels', []),
                    'has_attachments': email.get('has_attachments', False),
                    'pdf_attachments': email.get('pdf_attachments', []),
                    'processed_at': processed_at
                }
                formatted_emails.append(formatted_email)
                
            except Exception as e:
                print(f"Error formatting email {email.get('_id')}: {e}")
                continue
        
        # Add more debug logging
        print(f"Successfully formatted {len(formatted_emails)} emails")
        
        response = {
            "total": len(formatted_emails),
            "emails": formatted_emails
        }
        
        # Final debug log
        print(f"Sending response with {len(formatted_emails)} emails")
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Error in get_stored_emails: {e}")
        return jsonify({"error": str(e), "emails": []}), 500

@app.route('/api/attachment/<attachment_id>')
def get_attachment(attachment_id):
    try:
        # Convert string ID to ObjectId
        attachment = attachments_collection.find_one({"_id": ObjectId(attachment_id)})
        if not attachment:
            return jsonify({"error": "Attachment not found"}), 404
            
        return jsonify({
            "filename": attachment["filename"],
            "content": attachment["content"]  # Base64 encoded PDF
        })
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/attachments')
def get_attachments():
    try:
        # Get all PDF attachments
        attachments = list(attachments_collection.find(
            {},
            {
                'filename': 1,
                'email_id': 1,
                'upload_date': 1,
                '_id': 1
            }
        ).sort('upload_date', -1))
        
        # Convert ObjectId and dates to strings
        for attachment in attachments:
            attachment['id'] = str(attachment['_id'])
            attachment['upload_date'] = attachment['upload_date'].isoformat() if attachment.get('upload_date') else None
            del attachment['_id']
            
        return jsonify({
            "total": len(attachments),
            "attachments": attachments
        })
    except Exception as e:
        print(f"Error fetching attachments: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/schedules')
def get_schedules():
    try:
        schedules = list(schedules_collection.find(
            {},
            {
                'type': 1,
                'scheduled_date': 1,
                'location': 1,
                'meeting_link': 1,
                'subject': 1,
                'processed_at': 1,
                '_id': 0
            }
        ).sort('scheduled_date', -1))
        
        # Convert dates and handle None values
        for schedule in schedules:
            try:
                if schedule.get('scheduled_date'):
                    if isinstance(schedule['scheduled_date'], str):
                        schedule['scheduled_date'] = schedule['scheduled_date']
                    else:
                        schedule['scheduled_date'] = schedule['scheduled_date'].isoformat()
                else:
                    schedule['scheduled_date'] = datetime.now().isoformat()

                if schedule.get('processed_at'):
                    if isinstance(schedule['processed_at'], str):
                        schedule['processed_at'] = schedule['processed_at']
                    else:
                        schedule['processed_at'] = schedule['processed_at'].isoformat()
                else:
                    schedule['processed_at'] = datetime.now().isoformat()

                # Ensure type is valid
                if not schedule.get('type') or schedule['type'] not in ['meeting', 'exam', 'assignment', 'interview', 'other']:
                    schedule['type'] = 'other'

                # Ensure subject exists
                if not schedule.get('subject'):
                    schedule['subject'] = 'Untitled Event'

            except Exception as e:
                print(f"Error processing schedule: {e}")
                # Provide default values if processing fails
                schedule['scheduled_date'] = datetime.now().isoformat()
                schedule['processed_at'] = datetime.now().isoformat()
                schedule['type'] = 'other'
                schedule['subject'] = 'Untitled Event'

        print(f"Returning {len(schedules)} schedules")
        return jsonify({
            "total": len(schedules),
            "schedules": schedules
        })
    except Exception as e:
        print(f"Error fetching schedules: {e}")
        return jsonify({
            "error": str(e),
            "schedules": []
        }), 500

@app.route('/api/categorized-emails')
def get_categorized_emails():
    try:
        print("\nFetching all emails including spam...")
        
        # Get regular emails
        regular_emails = list(emails_collection.find({}).sort([
            ('date', -1),
            ('processed_at', -1)
        ]))
        
        # Get spam emails
        spam_emails = list(spam_emails_collection.find({}).sort([
            ('date', -1),
            ('processed_at', -1)
        ]))
        
        categorized_emails = []
        
        # Process regular emails
        for email in regular_emails:
            try:
                email_id = str(email['_id'])
                
                # Format date if it exists, otherwise use processed_at
                try:
                    if isinstance(email.get('date'), str):
                        date = email['date']
                    else:
                        date = email.get('processed_at', datetime.now()).isoformat()
                except:
                    date = datetime.now().isoformat()
                
                # Ensure sender is properly formatted
                sender = email.get('sender', 'Unknown Sender')
                if not sender or sender.strip() == '':
                    sender = 'Unknown Sender'
                
                email_doc = {
                    'id': email_id,
                    'subject': email.get('subject', 'No Subject'),
                    'sender': sender,
                    'date': date,
                    'body': email.get('body', ''),
                    'summary': email.get('summary', ''),
                    'category': email.get('category', 'primary'),
                    'isRead': email.get('isRead', False),
                    'isStarred': email.get('isStarred', False),
                    'labels': email.get('labels', []),
                    'has_attachments': email.get('has_attachments', False),
                    'pdf_attachments': email.get('pdf_attachments', []),
                    'processed_at': email.get('processed_at', datetime.now()).isoformat()
                }
                
                categorized_emails.append(email_doc)
                
            except Exception as e:
                print(f"Error processing regular email {email.get('_id')}: {e}")
                continue
        
        # Process spam emails
        for spam in spam_emails:
            try:
                spam_id = str(spam['_id'])
                
                spam_doc = {
                    'id': spam_id,
                    'subject': spam.get('subject', 'No Subject'),
                    'sender': spam.get('sender', 'Unknown Sender'),
                    'date': spam.get('date', ''),
                    'body': spam.get('body', ''),
                    'summary': 'Spam email',  # Default summary for spam
                    'category': 'spam',  # Always mark as spam
                    'isRead': spam.get('isRead', False),
                    'isStarred': spam.get('isStarred', False),
                    'labels': ['spam'],  # Add spam label
                    'has_attachments': spam.get('has_attachments', False),
                    'pdf_attachments': spam.get('pdf_attachments', []),
                    'processed_at': spam.get('processed_at', datetime.now()).isoformat(),
                    'detected_at': spam.get('detected_at', datetime.now()).isoformat()
                }
                
                categorized_emails.append(spam_doc)
                
            except Exception as e:
                print(f"Error processing spam email {spam.get('_id')}: {e}")
                continue

        print(f"Successfully fetched {len(categorized_emails)} total emails")
        print(f"Regular emails: {len(regular_emails)}")
        print(f"Spam emails: {len(spam_emails)}")
        
        return jsonify({
            'emails': sorted(
                categorized_emails,
                key=lambda x: datetime.fromisoformat(str(x['processed_at']).replace('Z', '+00:00')),
                reverse=True
            )
        })
        
    except Exception as e:
        print(f"Error in get_categorized_emails: {e}")
        return jsonify({"error": str(e)}), 500

def categorize_email(email):
    """Enhanced email categorization with spam detection"""
    content = f"{email['subject']} {email['body']}".lower()
    sender = email['sender'].lower()
    
    # Spam Detection
    spam_indicators = [
        # Common spam phrases
        'win', 'winner', 'congratulation', 'prize', 'lottery',
        'million dollar', 'inheritance', 'bank transfer',
        'nigerian prince', 'investment opportunity',
        'earn money fast', 'work from home', 'make money online',
        'casino', 'betting', 'gambling',
        'viagra', 'pharmacy', 'medication',
        'weight loss', 'diet pill',
        'luxury replica', 'rolex',
        
        # Suspicious urgency
        'urgent', 'act now', 'limited time', 'exclusive deal',
        'once in a lifetime', 'don\'t miss out',
        
        # Financial scams
        'bank account verify', 'account suspended',
        'credit card verify', 'billing information',
        'payment pending', 'invoice attached',
        
        # Suspicious domains (check sender)
        '.xyz', '.top', '.loan', '.work', '.click',
        
        # Cryptocurrency scams
        'bitcoin', 'cryptocurrency', 'crypto investment',
        'blockchain opportunity', 'mining profit',
        
        # Adult content indicators
        'adult', 'dating', 'singles in your area',
        
        # Suspicious formatting
        '100% free', '100% satisfied',
        'best price', 'cheap', 'discount',
        'fast cash', 'free access', 'free consultation',
        'free gift', 'free hosting', 'free info',
        'free investment', 'free membership',
        'free money', 'free preview', 'free quote',
        'free website'
    ]

    # Check for spam indicators
    spam_count = sum(1 for indicator in spam_indicators if indicator in content)
    if spam_count >= 2 or any(indicator in sender for indicator in ['.xyz', '.top', '.loan', '.work', '.click']):
        return 'spam'
    
    # Rest of your existing categorization logic
    if any(term in content for term in [
        'password reset', 'otp', 'verification code'
        # ... rest of your conditions
    ]):
        return 'temporary'
    
    # ... rest of your existing categories ...
    
    return 'primary'  # Default category

def summarize_email(subject, body):
    try:
        # Truncate body if it's too long (roughly 1000 words)
        truncated_body = ' '.join(body.split()[:1000]) if body else ''
        
        completion = client.chat.completions.create(
            model="google/gemini-flash-1.5-8b",
            messages=[{
                "role": "user",
                "content": f"""Summarize this email in one sentence:
                    
                    Subject: {subject}
                    Body: {truncated_body}"""
            }],
            max_tokens=100  # Limit response length
        )
        
        if not completion or not hasattr(completion, 'choices') or not completion.choices:
            return "Unable to generate summary"
            
        message_content = completion.choices[0].message.content
        if not message_content:
            return "No summary generated"
            
        return message_content
        
    except Exception as e:
        print(f"Error summarizing email: {str(e)}")
        print(f"Subject: {subject}")
        print(f"Body preview: {body[:100] if body else 'No body'}")
        return "Error in summarization"

@app.route('/api/dashboard-stats')
def get_dashboard_stats():
    try:
        # Only get non-spam emails
        inbox_query = {
            "$and": [
                {"folder": "inbox"},  # Only include inbox emails
                {"category": {"$ne": "spam"}},  # Exclude spam category
                {"folder": {"$ne": "spam"}}  # Double check to exclude spam folder
            ]
        }

        # Get total emails (excluding spam)
        total_emails = emails_collection.count_documents(inbox_query)

        # Get category counts (excluding spam)
        category_counts = list(emails_collection.aggregate([
            {
                "$match": inbox_query
            },
            {
                "$group": {
                    "_id": "$category",
                    "count": {"$sum": 1}
                }
            }
        ]))

        # Get recent emails (excluding spam)
        recent_emails = list(emails_collection.find(
            inbox_query,
            {
                "subject": 1,
                "sender": 1,
                "date": 1,
                "category": 1,
                "_id": 0
            }
        ).sort("date", -1).limit(5))

        return jsonify({
            "total_emails": total_emails,
            "category_distribution": {item["_id"]: item["count"] for item in category_counts},
            "recent_emails": recent_emails
        })

    except Exception as e:
        print(f"Error getting dashboard stats: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/emails/<email_id>')
def get_single_email(email_id):
    try:
        # Try to find email in regular emails collection
        email = emails_collection.find_one({"_id": ObjectId(email_id)})
        
        # If not found in regular emails, check spam collection
        if not email:
            email = spam_emails_collection.find_one({"_id": ObjectId(email_id)})
            
        if not email:
            return jsonify({"error": "Email not found"}), 404

        # Convert MongoDB ObjectId to string
        email['_id'] = str(email['_id'])
        
        return jsonify(email)
        
    except Exception as e:
        print(f"Error fetching single email: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        query = data.get('query')
        
        if not query:
            return jsonify({"error": "No query provided"}), 400
            
        # Import the search_emails function
        from email_search_service import search_emails
        
        # Get response from email search service
        response = search_emails(query)
        
        return jsonify({
            "response": response
        })
        
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return jsonify({
            "error": "Internal server error",
            "details": str(e)
        }), 500

if __name__ == '__main__':
    print("Starting Flask server...")
    try:
        print("Server will be available at http://localhost:5001")
        app.run(host='0.0.0.0', port=5001, debug=True)
    except Exception as e:
        print(f"Failed to start server: {e}") 