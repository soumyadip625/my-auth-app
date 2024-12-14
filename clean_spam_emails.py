from pymongo import MongoClient
from datetime import datetime

# MongoDB setup
MONGO_URI = "mongodb://localhost:27017"
client = MongoClient(MONGO_URI)
db = client.email_dashboard
emails_collection = db.emails

def clean_spam_emails():
    try:
        print("\nStarting spam cleanup...")
        
        # Get total emails before cleanup
        total_before = emails_collection.count_documents({})
        print(f"Total emails before cleanup: {total_before}")
        
        # Delete emails that are either in spam folder or have spam category
        result = emails_collection.delete_many({
            "$or": [
                {"folder": "spam"},
                {"category": "spam"}
            ]
        })
        
        # Get total emails after cleanup
        total_after = emails_collection.count_documents({})
        
        print("\nCleanup Summary:")
        print(f"Spam emails deleted: {result.deleted_count}")
        print(f"Emails remaining: {total_after}")

    except Exception as e:
        print(f"Error during cleanup: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    clean_spam_emails() 