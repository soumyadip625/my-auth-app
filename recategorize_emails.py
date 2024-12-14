from pymongo import MongoClient
from email_service import categorize_email

# MongoDB setup
MONGO_URI = "mongodb://localhost:27017"
client = MongoClient(MONGO_URI)
db = client.email_dashboard
emails_collection = db.emails

def recategorize_all_emails():
    try:
        print("\nStarting email recategorization...")
        
        # Get all emails
        emails = list(emails_collection.find({}))
        total = len(emails)
        print(f"Found {total} emails to recategorize")
        
        # Update categories
        for i, email in enumerate(emails, 1):
            new_category = categorize_email({
                'subject': email.get('subject', ''),
                'body': email.get('body', ''),
                'sender': email.get('sender', '')
            })
            
            emails_collection.update_one(
                {'_id': email['_id']},
                {'$set': {'category': new_category}}
            )
            
            if i % 10 == 0:
                print(f"Processed {i}/{total} emails")
        
        # Get category counts
        categories = emails_collection.distinct('category')
        for category in categories:
            count = emails_collection.count_documents({'category': category})
            print(f"{category}: {count} emails")
            
    except Exception as e:
        print(f"Error during recategorization: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    recategorize_all_emails() 