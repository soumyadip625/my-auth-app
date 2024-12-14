import imaplib
import email
from email.header import decode_header
from datetime import datetime, timedelta
import os
from pymongo import MongoClient
from dotenv import load_dotenv
import base64
import schedule
import time

# Load environment variables
load_dotenv()

# MongoDB setup
MONGO_URI = "mongodb://localhost:27017"
client = MongoClient(MONGO_URI)
db = client.email_dashboard
spam_emails_collection = db.spam_emails  # New separate collection for spam
attachments_collection = db.pdf_attachments

# Email credentials
EMAIL = os.getenv('GMAIL_EMAIL')
PASSWORD = os.getenv('GMAIL_APP_PASSWORD')
IMAP_SERVER = "imap.gmail.com"

def decode_email_body(email_message):
    """Extract full email body with better error handling"""
    body = ""
    if email_message.is_multipart():
        for part in email_message.walk():
            if part.get_content_type() == "text/plain":
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        body = payload.decode('utf-8', errors='replace')
                        break
                except Exception as e:
                    print(f"Error decoding part: {e}")
                    continue
    else:
        try:
            payload = email_message.get_payload(decode=True)
            if payload:
                body = payload.decode('utf-8', errors='replace')
        except Exception as e:
            print(f"Error decoding body: {e}")
            body = "Could not decode email body"
    
    return body or "No readable content"

def process_spam_email(mail, num):
    """Process a single spam email and store it in spam collection"""
    try:
        # Check if email already exists in spam collection
        if spam_emails_collection.find_one({"email_id": int(num)}):
            print("Spam email already exists, skipping...")
            return

        # Fetch email data
        _, msg_data = mail.fetch(num, "(RFC822)")
        email_body = msg_data[0][1]
        email_message = email.message_from_bytes(email_body)

        # Get subject
        subject = decode_header(email_message["subject"] or "No Subject")[0][0]
        if isinstance(subject, bytes):
            subject = subject.decode()
        print(f"Subject: {subject}")

        # Get sender
        sender = email.utils.parseaddr(email_message["from"])[1]
        print(f"From: {sender}")

        # Get date
        date = email_message["date"]

        # Get body
        body = decode_email_body(email_message)
        
        # Process attachments
        pdf_attachments = []
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "application/pdf":
                    try:
                        filename = part.get_filename()
                        if filename:
                            print(f"Processing PDF: {filename}")
                            pdf_content = base64.b64encode(part.get_payload(decode=True)).decode()
                            attachment_doc = {
                                "filename": filename,
                                "content": pdf_content,
                                "email_id": num.decode(),
                                "upload_date": datetime.now(),
                                "is_spam": True  # Mark attachment as from spam
                            }
                            attachment_id = attachments_collection.insert_one(attachment_doc).inserted_id
                            pdf_attachments.append({
                                "filename": filename,
                                "id": str(attachment_id)
                            })
                    except Exception as e:
                        print(f"Error processing PDF: {e}")

        # Store in MongoDB spam collection
        spam_email_doc = {
            "email_id": int(num),
            "subject": subject,
            "sender": sender,
            "date": date,
            "body": body,
            "has_attachments": len(pdf_attachments) > 0,
            "pdf_attachments": pdf_attachments,
            "processed_at": datetime.now(),
            "isRead": False,
            "isStarred": False,
            "detected_at": datetime.now()
        }

        result = spam_emails_collection.insert_one(spam_email_doc)
        print(f"Stored spam email successfully (ID: {result.inserted_id})")
        return True

    except Exception as e:
        print(f"Error processing spam email: {e}")
        return False

def fetch_spam_emails():
    """Fetch historical spam emails since November 10th, 2024"""
    try:
        print("\nConnecting to Gmail...")
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, PASSWORD)
        
        print("\nAccessing Spam folder...")
        mail.select('[Gmail]/Spam')
        
        date_since = "10-Nov-2024"
        search_criteria = f'(SINCE "{date_since}")'
        print(f"Searching for spam emails since {date_since}...")
        
        _, message_numbers = mail.search(None, search_criteria)
        email_ids = message_numbers[0].split()
        total_emails = len(email_ids)
        print(f"Found {total_emails} spam emails")

        processed_count = 0
        error_count = 0

        for num in email_ids:
            processed_count += 1
            print(f"\nProcessing spam email {processed_count}/{total_emails}")
            if not process_spam_email(mail, num):
                error_count += 1

        print("\nSpam Processing Summary:")
        print(f"Total spam emails found: {total_emails}")
        print(f"Successfully processed: {processed_count - error_count}")
        print(f"Errors encountered: {error_count}")

        mail.close()
        mail.logout()

    except Exception as e:
        print(f"Error: {e}")

def check_new_spam():
    """Check for new spam emails in the last 5 minutes"""
    try:
        print("\nChecking for new spam emails...")
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, PASSWORD)
        
        print("\nChecking spam folder...")
        mail.select('[Gmail]/Spam')
        
        five_mins_ago = (datetime.now() - timedelta(minutes=5)).strftime("%d-%b-%Y")
        search_criteria = f'(SINCE "{five_mins_ago}")'
        _, message_numbers = mail.search(None, search_criteria)
        email_ids = message_numbers[0].split()
        
        if not email_ids:
            print("No new spam emails")
            return
        
        print(f"Found {len(email_ids)} new spam emails")
        for num in email_ids:
            process_spam_email(mail, num)

        mail.logout()
        print("Spam check completed")

    except Exception as e:
        print(f"Error checking spam emails: {e}")

def run_spam_service():
    """Run both initial fetch and continuous monitoring of spam"""
    print("Starting spam email service...")
    
    # First, fetch historical spam emails
    print("\nFetching historical spam emails...")
    fetch_spam_emails()
    
    # Then start continuous monitoring
    print("\nStarting continuous spam monitoring...")
    print("Will check for new spam every 5 minutes")
    
    # Schedule continuous checks
    schedule.every(5).minutes.do(check_new_spam)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    run_spam_service() 