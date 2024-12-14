from pymongo import MongoClient
from email_service import categorize_email

# MongoDB setup
MONGO_URI = "mongodb://localhost:27017"
client = MongoClient(MONGO_URI)
db = client.email_dashboard
emails_collection = db.emails

def find_and_categorize_promotions():
    try:
        print("\nAnalyzing emails for promotional content...")
        
        # Get all emails
        emails = list(emails_collection.find({}))
        total = len(emails)
        promo_count = 0
        
        print(f"Found {total} emails to analyze")
        
        for i, email in enumerate(emails, 1):
            content = f"{email.get('subject', '')} {email.get('body', '')}".lower()
            
            # Recategorize using updated logic
            new_category = categorize_email({
                'subject': email.get('subject', ''),
                'body': email.get('body', ''),
                'sender': email.get('sender', '')
            })
            
            if new_category == 'promotions':
                promo_count += 1
                print(f"Found promotional email: {email.get('subject', 'No Subject')}")
                
                emails_collection.update_one(
                    {'_id': email['_id']},
                    {'$set': {'category': 'promotions'}}
                )
            
            if i % 10 == 0:
                print(f"Processed {i}/{total} emails")
        
        print(f"\nSummary:")
        print(f"Total emails analyzed: {total}")
        print(f"Promotional emails found: {promo_count}")
        
    except Exception as e:
        print(f"Error during promotion analysis: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    find_and_categorize_promotions() 