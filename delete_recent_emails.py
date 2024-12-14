from pymongo import MongoClient
from datetime import datetime

# MongoDB setup
MONGO_URI = "mongodb://localhost:27017"
client = MongoClient(MONGO_URI)
db = client.email_dashboard
emails_collection = db.emails

def delete_recent_emails():
    try:
        print("\nStarting email deletion...")
        
        # Get total emails before deletion
        total_before = emails_collection.count_documents({})
        print(f"Total emails before deletion: {total_before}")
        
        # Get the last 62 emails sorted by processed_at
        emails_to_delete = list(emails_collection.find().sort('processed_at', -1).limit(62))
        
        # Delete these emails
        for email in emails_to_delete:
            emails_collection.delete_one({'_id': email['_id']})
        
        # Get total emails after deletion
        total_after = emails_collection.count_documents({})
        
        print("\nDeletion Summary:")
        print(f"Emails deleted: {len(emails_to_delete)}")
        print(f"Emails remaining: {total_after}")

    except Exception as e:
        print(f"Error during deletion: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    delete_recent_emails() 