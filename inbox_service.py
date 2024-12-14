import schedule
import time
import imaplib
import email
from email.header import decode_header
from datetime import datetime, timedelta
import os
from pymongo import MongoClient
from dotenv import load_dotenv
import base64

# Load environment variables
load_dotenv()

# MongoDB setup
MONGO_URI = "mongodb://localhost:27017"
client = MongoClient(MONGO_URI)
db = client.email_dashboard
emails_collection = db.emails
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

def check_new_emails():
    try:
        print("\nChecking for new emails...")
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, PASSWORD)
        
        # Check both inbox and spam folder
        for folder in ['INBOX', '[Gmail]/Spam']:
            try:
                print(f"\nChecking folder: {folder}")
                mail.select(folder)
                
                # Search for recent emails (last 5 minutes)
                five_mins_ago = (datetime.now() - timedelta(minutes=5)).strftime("%d-%b-%Y")
                search_criteria = f'(SINCE "{five_mins_ago}")'
                _, message_numbers = mail.search(None, search_criteria)
                email_ids = message_numbers[0].split()
                
                if not email_ids:
                    print(f"No new emails in {folder}")
                    continue
                
                print(f"Found {len(email_ids)} new emails in {folder}")

                for num in email_ids:
                    try:
                        # Check if email already exists
                        if emails_collection.find_one({"email_id": int(num)}):
                            print("Email already exists, skipping...")
                            continue

                        # Fetch email data
                        _, msg_data = mail.fetch(num, "(RFC822)")
                        email_body = msg_data[0][1]
                        email_message = email.message_from_bytes(email_body)

                        # Get subject
                        subject = decode_header(email_message["subject"] or "No Subject")[0][0]
                        if isinstance(subject, bytes):
                            subject = subject.decode()

                        # Get sender
                        sender = email.utils.parseaddr(email_message["from"])[1]

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
                                                "upload_date": datetime.now()
                                            }
                                            attachment_id = attachments_collection.insert_one(attachment_doc).inserted_id
                                            pdf_attachments.append({
                                                "filename": filename,
                                                "id": str(attachment_id)
                                            })
                                    except Exception as e:
                                        print(f"Error processing PDF: {e}")

                        # Store in MongoDB
                        email_doc = {
                            "email_id": int(num),
                            "subject": subject,
                            "sender": sender,
                            "date": date,
                            "body": body,
                            "category": "spam" if folder == '[Gmail]/Spam' else "primary",
                            "has_attachments": len(pdf_attachments) > 0,
                            "pdf_attachments": pdf_attachments,
                            "processed_at": datetime.now(),
                            "isRead": False,
                            "isStarred": False,
                            "folder": "spam" if folder == '[Gmail]/Spam' else "inbox"
                        }

                        result = emails_collection.insert_one(email_doc)
                        print(f"Stored new email successfully (ID: {result.inserted_id})")

                    except Exception as e:
                        print(f"Error processing email: {e}")
                        continue

            except Exception as e:
                print(f"Error checking folder {folder}: {e}")
                continue

        mail.logout()
        print("Email check completed")

    except Exception as e:
        print(f"Error checking emails: {e}")

def run_inbox_service():
    print("Starting inbox service...")
    print("Will check for new emails every 5 minutes")
    
    # Run initial check
    check_new_emails()
    
    # Schedule to run every 5 minutes
    schedule.every(5).minutes.do(check_new_emails)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    run_inbox_service() 