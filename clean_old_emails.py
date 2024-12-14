from pymongo import MongoClient
from datetime import datetime
import email.utils
from dotenv import load_dotenv
import os
from datetime import timezone

# Load environment variables
load_dotenv()

# MongoDB setup
MONGO_URI = "mongodb://localhost:27017"
client = MongoClient(MONGO_URI)
db = client.email_dashboard
emails_collection = db.emails
attachments_collection = db.pdf_attachments

def parse_email_date(date_str):
    try:
        # Parse email date string to timestamp (returns timezone-aware datetime)
        parsed_date = email.utils.parsedate_to_datetime(date_str)
        if parsed_date is None:
            return None
        # Convert to UTC if it's not already
        if parsed_date.tzinfo is None:
            parsed_date = parsed_date.replace(tzinfo=timezone.utc)
        return parsed_date
    except:
        return None

def clean_old_emails():
    try:
        print("\nStarting email cleanup...")
        
        # Set cutoff date to November 10th, 2024 (UTC)
        cutoff_date = datetime(2024, 11, 10, tzinfo=timezone.utc)
        print(f"Cutoff date: {cutoff_date}")

        # Get total emails before cleanup
        total_before = emails_collection.count_documents({})
        print(f"Total emails before cleanup: {total_before}")

        # Find emails to delete
        old_emails = list(emails_collection.find({}))
        deleted_count = 0
        attachment_count = 0

        for email in old_emails:
            date = parse_email_date(email.get('date'))
            if date is None:
                print(f"Warning: Could not parse date for email {email['_id']}")
                continue
                
            if date < cutoff_date:
                print(f"Deleting email from {date}")
                # Delete associated attachments first
                if email.get('pdf_attachments'):
                    for attachment in email['pdf_attachments']:
                        try:
                            attachments_collection.delete_one({'_id': attachment.get('id')})
                            attachment_count += 1
                        except Exception as e:
                            print(f"Error deleting attachment: {e}")
                
                # Delete the email
                emails_collection.delete_one({'_id': email['_id']})
                deleted_count += 1

        # Get total emails after cleanup
        total_after = emails_collection.count_documents({})

        print("\nCleanup Summary:")
        print(f"Emails deleted: {deleted_count}")
        print(f"Attachments deleted: {attachment_count}")
        print(f"Emails remaining: {total_after}")

    except Exception as e:
        print(f"Error during cleanup: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    clean_old_emails() 