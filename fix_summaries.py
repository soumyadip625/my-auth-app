from pymongo import MongoClient
from email_service import summarize_email
import time
import logging

# Set up logging
logging.basicConfig(filename='summary_fix_log.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# MongoDB setup
MONGO_URI = "mongodb://localhost:27017"
client = MongoClient(MONGO_URI)
db = client.email_dashboard
emails_collection = db.emails

def fix_email_summaries():
    try:
        print("\nChecking for emails with missing or error summaries...")
        
        # Find emails with problematic summaries
        problem_emails = emails_collection.find({
            "$or": [
                {"summary": None},
                {"summary": ""},
                {"summary": "Error in summarization"},
                {"summary": "Unable to generate summary"},
                {"summary": "No summary generated"}
            ]
        })
        
        total = emails_collection.count_documents({
            "$or": [
                {"summary": None},
                {"summary": ""},
                {"summary": "Error in summarization"},
                {"summary": "Unable to generate summary"},
                {"summary": "No summary generated"}
            ]
        })
        
        print(f"Found {total} emails needing summary fixes")
        
        fixed_count = 0
        for i, email in enumerate(problem_emails, 1):
            try:
                # Get new summary
                new_summary = summarize_email(
                    email.get('subject', ''),
                    email.get('body', '')
                )
                
                # Add delay to avoid rate limits
                time.sleep(2)
                
                # Update if we got a valid summary
                if new_summary and "error" not in new_summary.lower():
                    emails_collection.update_one(
                        {'_id': email['_id']},
                        {'$set': {'summary': new_summary}}
                    )
                    fixed_count += 1
                    print(f"Fixed summary for: {email.get('subject', 'No Subject')}")
                    print(f"New summary: {new_summary}\n")
                else:
                    logging.error(f"Failed to generate summary for email {email.get('_id')}: {new_summary}")
                
                if i % 5 == 0:
                    print(f"Processed {i}/{total} emails")
                    
            except Exception as e:
                logging.error(f"Error fixing summary for email {email.get('_id')}: {e}")
                continue
        
        print(f"\nSummary Fix Results:")
        print(f"Total emails processed: {total}")
        print(f"Successfully fixed: {fixed_count}")
        
    except Exception as e:
        logging.error(f"Error during summary fix process: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    fix_email_summaries()
