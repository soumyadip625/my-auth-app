import imaplib
import email
from email.header import decode_header
from datetime import datetime
import os
from pymongo import MongoClient
from dotenv import load_dotenv
import base64
from app import categorize_email

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

def fetch_historical_emails():
    try:
        print("\nConnecting to Gmail...")
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, PASSWORD)
        
        # Fetch from both inbox and spam folder
        for folder in ['INBOX', '[Gmail]/Spam']:
            try:
                print(f"\nProcessing folder: {folder}")
                mail.select(folder)
                
                # Search for emails from November 10th, 2024
                date_since = "10-Nov-2024"
                search_criteria = f'(SINCE "{date_since}")'
                _, message_numbers = mail.search(None, search_criteria)
                
                email_ids = message_numbers[0].split()
                total_emails = len(email_ids)
                print(f"Found {total_emails} emails")

                processed_count = 0
                error_count = 0

                for num in email_ids:
                    try:
                        processed_count += 1
                        print(f"\nProcessing email {processed_count}/{total_emails}")
                        
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
                        print(f"Subject: {subject}")

                        # Get sender
                        sender = email.utils.parseaddr(email_message["from"])[1]
                        print(f"From: {sender}")

                        # Get date
                        date = email_message["date"]

                        # Get full body
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
                            "category": categorize_email({
                                'subject': subject,
                                'body': body,
                                'sender': sender
                            }),
                            "has_attachments": len(pdf_attachments) > 0,
                            "pdf_attachments": pdf_attachments,
                            "processed_at": datetime.now(),
                            "isRead": False,
                            "isStarred": False,
                            "folder": "inbox"
                        }

                        result = emails_collection.insert_one(email_doc)
                        print(f"Stored email successfully (ID: {result.inserted_id})")

                    except Exception as e:
                        error_count += 1
                        print(f"Error processing email: {e}")
                        continue

            except Exception as e:
                print(f"Error processing folder {folder}: {e}")
                continue

        mail.close()
        mail.logout()

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Starting historical email fetch...")
    fetch_historical_emails() 