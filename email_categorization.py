import time
from datetime import datetime
from pymongo import MongoClient
from email_service import categorize_email  # Import the categorize_email function

# MongoDB connection details
MONGO_URI = "mongodb://localhost:27017"
DATABASE_NAME = "email_dashboard"
COLLECTION_NAME = "emails"

# Connect to the MongoDB database
def connect_to_database():
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    return db[COLLECTION_NAME]

# Fetch email summaries from the database
def fetch_email_summaries(collection):
    emails = collection.find({}, {"summary": 1, "subject": 1, "body": 1, "sender": 1})
    return [email for email in emails]

# Main function to run the email categorization process
def main():
    while True:
        print(f"[{datetime.now()}] Fetching and categorizing emails...")
        try:
            # Connect to the database
            collection = connect_to_database()
            
            # Fetch email summaries
            email_summaries = fetch_email_summaries(collection)
            
            # Categorize emails
            for email in email_summaries:
                category = categorize_email({
                    'subject': email.get('subject', ''),
                    'body': email.get('body', ''),
                    'sender': email.get('sender', '')
                })
                print(f"Email from {email.get('sender', 'Unknown Sender')} categorized as: {category}")
                # Update the email document with the category
                collection.update_one({"_id": email["_id"]}, {"$set": {"category": category}})
            
        except Exception as e:
            print(f"Error: {e}")
        
        # Sleep for a while before the next iteration
        time.sleep(60)

if __name__ == "__main__":
    main()
