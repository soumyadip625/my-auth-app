import schedule
import time
import imaplib
import email
from email.header import decode_header
from datetime import datetime, timedelta
import os
from pymongo import MongoClient
from dotenv import load_dotenv
import requests
import base64
from openai import OpenAI
import re
import logging

# Set up logging
logging.basicConfig(filename='email_service_log.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# MongoDB setup
MONGO_URI = "mongodb://localhost:27017"
client = MongoClient(MONGO_URI)
db = client.email_dashboard
emails_collection = db.emails
attachments_collection = db.pdf_attachments
try:
    # First, remove any documents with null message_ids
    emails_collection.delete_many({"message_id": None})
    # Then create the unique index, if it doesn't exist
    emails_collection.create_index("message_id", unique=True, sparse=True)
except Exception as e:
    print(f"Index creation warning: {e}")

# Email credentials
EMAIL = os.getenv('GMAIL_EMAIL')
PASSWORD = os.getenv('GMAIL_APP_PASSWORD')
IMAP_SERVER = "imap.gmail.com"

# OpenAI setup
openai_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv('OPENROUTER_API_KEY'),
    default_headers={
        "HTTP-Referer": "http://localhost:3000",  # Required for OpenRouter
        "X-Title": "Email Summary Service"  # Optional - your app's name
    }
)

def categorize_email(email_content):
    """Enhanced email categorization logic"""
    content = f"{email_content['subject']} {email_content['body']}".lower()
    sender = email_content.get('sender', '').lower()
    
    # Enhanced promotion detection
    promotion_indicators = [
        # Marketing terms
        'promotion', 'offer', 'discount', 'sale', 'deal', 'coupon',
        'special offer', 'limited time', 'exclusive', 'savings',
        # Shopping terms
        'shop now', 'buy now', 'order today', 'free shipping',
        'new arrival', 'clearance', 'flash sale', 'best seller',
        # Urgency terms
        'last chance', 'ending soon', 'don\'t miss out', 'limited stock',
        # Percentage and money terms
        '% off', 'cashback', 'free gift', 'bonus',
        # Common promotional phrases
        'black friday', 'cyber monday', 'holiday sale',
        'seasonal offer', 'members only', 'vip offer',
        # Newsletter and updates
        'newsletter', 'latest deals', 'weekly offers',
        # Common promotional senders
        'amazon', 'flipkart', 'ebay', 'walmart',
        'unsubscribe', 'marketing', 'promotional'
    ]
    
    # Check for promotional content
    promo_count = sum(1 for indicator in promotion_indicators if indicator in content)
    if promo_count >= 2 or 'unsubscribe' in content.lower():
        return 'promotions'
        
    # Spam Detection
    spam_indicators = [
        'win', 'winner', 'prize', 'lottery', 'million dollar', 'inheritance',
        'bank transfer', 'investment opportunity', 'casino', 'betting',
        'viagra', 'pharmacy', 'weight loss', 'luxury replica',
        'urgent', 'act now', 'limited time', 'exclusive deal',
        'bank account verify', 'account suspended', 'payment pending',
        '.xyz', '.top', '.loan', '.work', '.click'
    ]
    
    spam_count = sum(1 for indicator in spam_indicators if indicator in content)
    if spam_count >= 2 or any(indicator in sender for indicator in ['.xyz', '.top', '.loan', '.work', '.click']):
        return 'spam'
    
    # Enhanced categories with more specific patterns
    categories = {
        'finance': [
            'invoice', 'payment', 'bill', 'transaction', 'credit', 'debit', 'bank', 'salary',
            'receipt', 'subscription fee', 'account balance', 'statement'
        ],
        'meetings': [
            'meeting', 'schedule', 'appointment', 'calendar', 'zoom', 'google meet',
            'conference', 'discussion', 'sync up', 'catch up', 'team meeting'
        ],
        'education': [
            'course', 'lecture', 'assignment', 'homework', 'exam', 'quiz', 'study',
            'grade', 'certificate', 'training', 'workshop', 'webinar'
        ],
        'social': [
            'linkedin', 'facebook', 'twitter', 'instagram', 'social', 'connection', 'network',
            'invitation', 'connect', 'profile view', 'endorsement'
        ],
        'updates': [
            'newsletter', 'subscription', 'digest', 'weekly update', 'monthly update',
            'announcement', 'news', 'product update', 'release notes'
        ],
        'jobs': [
            'job', 'career', 'position', 'opportunity', 'hiring', 'recruitment',
            'interview', 'application', 'resume', 'offer letter', 'employment'
        ],
        'work': [
            'project', 'task', 'collaboration', 'deadline', 'review', 'feedback',
            'report', 'status update', 'milestone', 'deliverable'
        ],
        'promotions': [
            'promotion', 'offer', 'discount', 'sale', 'deal', 'coupon',
            'special offer', 'limited time', 'exclusive', 'savings'
        ],
        'development': [
            'github', 'gitlab', 'pull request', 'commit', 'merge', 'code review',
            'bug', 'feature', 'deployment', 'release', 'api', 'documentation'
        ],
        'security': [
            'password', 'security', 'verification', 'authenticate', '2fa', 'login',
            'access', 'permission', 'authorization', 'reset', 'suspicious'
        ],
        'travel': [
            'flight', 'booking', 'reservation', 'itinerary', 'travel', 'hotel',
            'ticket', 'boarding pass', 'accommodation', 'trip'
        ],
        'notifications': [
            'alert', 'notification', 'reminder', 'notice', 'action required',
            'confirmation', 'verify', 'validate', 'approve'
        ],
        'health': [
            'doctor', 'appointment', 'prescription', 'health', 'medical', 'hospital',
            'pharmacy', 'insurance', 'wellness', 'fitness', 'nutrition'
        ],
        'shopping': [
            'order', 'shipment', 'delivery', 'tracking', 'purchase', 'cart',
            'checkout', 'store', 'retail', 'product', 'catalog'
        ],
        'entertainment': [
            'movie', 'film', 'show', 'concert', 'event', 'ticket', 'booking',
            'streaming', 'music', 'game', 'play', 'theater'
        ],
        'real estate': [
            'property', 'listing', 'rent', 'sale', 'lease', 'mortgage',
            'real estate', 'home', 'apartment', 'condo', 'house'
        ],
        'legal': [
            'law', 'lawyer', 'legal', 'contract', 'agreement', 'court',
            'case', 'litigation', 'document', 'notice', 'complaint'
        ],
        'support': [
            'support', 'help', 'assistance', 'customer service', 'contact',
            'ticket', 'issue', 'resolution', 'feedback', 'query'
        ],
        'subscriptions': [
            'subscription', 'renewal', 'plan', 'billing', 'payment',
            'cancel', 'upgrade', 'downgrade', 'service', 'membership'
        ],
        'events': [
            'event', 'conference', 'seminar', 'workshop', 'webinar',
            'gathering', 'meetup', 'celebration', 'party', 'festival'
        ]
    }
    
    # Check content against each category
    for category, keywords in categories.items():
        if any(keyword in content for keyword in keywords):
            return category
    
    # If no specific category matches
    return 'general'

def summarize_email(subject, body):
    try:
        # Truncate body if it's too long (roughly 1000 words)
        truncated_body = ' '.join(body.split()[:1000]) if body else ''
        
        completion = openai_client.chat.completions.create(
            model="google/gemini-flash-1.5-8b",
            messages=[{
                "role": "user",
                "content": f"""Summarize this email in one sentence:
                    
                    Subject: {subject}
                    Body: {truncated_body}"""
            }],
            max_tokens=100
        )
        
        # Remove debug logging of API Response
        if not completion or not hasattr(completion, 'choices') or not completion.choices:
            logging.error("OpenAI API response is empty or invalid.")
            return "Unable to generate summary"
            
        message_content = completion.choices[0].message.content
        if not message_content:
            logging.error("OpenAI API response does not contain a summary.")
            return "No summary generated"
            
        return message_content
        
    except Exception as e:
        logging.error(f"Error summarizing email: {str(e)}")
        return "Error in summarization"

def check_new_emails():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, PASSWORD)
        mail.select('inbox')
        
        # Search for today's emails instead of just unread
        today = datetime.now().strftime("%d-%b-%Y")
        _, messages = mail.search(None, f'(SINCE "{today}")')
        
        if messages[0]:
            email_ids = messages[0].split()
            print(f"Found {len(email_ids)} emails from today")
            
            for num in email_ids:
                _, msg_data = mail.fetch(num, '(RFC822)')
                email_body = msg_data[0][1]
                email_msg = email.message_from_bytes(email_body)
                
                # Use Message-ID as unique identifier
                message_id = email_msg.get('Message-ID', '')
                
                # Skip if email already exists in database
                if emails_collection.find_one({"message_id": message_id}):
                    continue

                # Get basic email info
                subject = decode_header(email_msg["Subject"])[0][0]
                if isinstance(subject, bytes):
                    subject = subject.decode()
                
                # Get body
                body = ""
                if email_msg.is_multipart():
                    for part in email_msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode('utf-8', 'ignore')
                            break
                else:
                    body = email_msg.get_payload(decode=True).decode('utf-8', 'ignore')

                # Store email
                email_data = {
                    "message_id": message_id,
                    "subject": subject,
                    "sender": email_msg.get('From', 'Unknown Sender'),
                    "date": email_msg.get('Date'),
                    "body": body,
                    "summary": summarize_email(subject, body),
                    "category": categorize_email({
                        'subject': subject,
                        'body': body,
                        'sender': email_msg.get('From', '')
                    }),
                    "processed_at": datetime.now(),
                    "isRead": False,
                    "isStarred": False,
                    "labels": []
                }
                
                emails_collection.insert_one(email_data)
                print(f"Stored new email: {subject}")
        
        mail.close()
        mail.logout()
        
    except Exception as e:
        print(f"Error: {e}")

def run_service():
    print("\n=== Email Check Service Started ===")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Checking for new emails every 2 minutes...")
    print("Press Ctrl+C to stop the service")
    print("=====================================\n")
    
    # Run immediately on start
    check_new_emails()
    
    # Schedule future runs
    schedule.every(2).minutes.do(check_new_emails)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

def extract_time_slot(text):
    """Extract time slot from text"""
    try:
        time_patterns = [
            r'(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))\s*(?:to|-)\s*(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))',
            r'(\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm))',
            r'at\s+(\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm))',
            r'time:\s*(\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm))',
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if len(match.groups()) > 1:
                    return f"{match.group(1)} - {match.group(2)}"
                return match.group(1)
        return None
    except Exception as e:
        print(f"Error extracting time slot: {e}")
        return None

def extract_meeting_link(text):
    """Extract meeting link"""
    try:
        link_match = re.search(r'https?://[^\s<>"]+?(?:zoom|meet|teams)\.[^\s<>"]+', text)
        return link_match.group(0) if link_match else None
    except Exception as e:
        print(f"Error extracting link: {e}")
        return None

def extract_login_info(text):
    """Extract login ID"""
    try:
        login_match = re.search(r'login\s*(?:id)?:\s*([A-Za-z0-9_-]+)', text, re.IGNORECASE)
        return login_match.group(1) if login_match else None
    except Exception as e:
        print(f"Error extracting login: {e}")
        return None

def extract_password(text):
    """Extract password"""
    try:
        pwd_match = re.search(r'password:\s*([A-Za-z0-9@#$%^&+=]+)', text, re.IGNORECASE)
        return pwd_match.group(1) if pwd_match else None
    except Exception as e:
        print(f"Error extracting password: {e}")
        return None

def extract_event_info(email_content):
    """Extract event information from email"""
    content = f"{email_content['subject']} {email_content['body']}".lower()
    
    # Determine event type
    if any(word in content for word in ['exam', 'test', 'quiz', 'assessment']):
        event_type = 'exam'
    elif any(word in content for word in ['meeting', 'conference', 'call', 'discussion']):
        event_type = 'meeting'
    else:
        event_type = 'event'
        
    return {
        'type': event_type,
        'timeSlot': extract_time_slot(content),
        'link': extract_meeting_link(content) if event_type == 'meeting' else None,
        'loginId': extract_login_info(content) if event_type == 'exam' else None,
        'password': extract_password(content) if event_type == 'exam' else None
    }

if __name__ == "__main__":
    run_service()
