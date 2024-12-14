from pymongo import MongoClient
from datetime import datetime

# MongoDB setup
MONGO_URI = "mongodb://localhost:27017"
client = MongoClient(MONGO_URI)
db = client.email_dashboard
emails_collection = db.emails

def clean_emails():
    try:
        # Update emails without folder field
        result = emails_collection.update_many(
            {"folder": {"$exists": False}},
            {"$set": {"folder": "inbox"}}
        )
        print(f"Updated {result.modified_count} emails without folder field")

        # Update spam category emails to have spam folder
        result = emails_collection.update_many(
            {"category": "spam"},
            {"$set": {"folder": "spam"}}
        )
        print(f"Updated {result.modified_count} spam emails")

    except Exception as e:
        print(f"Error cleaning emails: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    clean_emails() 