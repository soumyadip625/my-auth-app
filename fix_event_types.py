from pymongo import MongoClient
from datetime import datetime
import re

# MongoDB setup
MONGO_URI = "mongodb://localhost:27017"
client = MongoClient(MONGO_URI)
db = client.email_dashboard
emails_collection = db.emails

def determine_event_type(subject, body):
    """Better event type detection"""
    content = f"{subject} {body}".lower()
    
    # Exam related patterns
    exam_patterns = [
        r'exam\s+schedule',
        r'test\s+date',
        r'quiz\s+time',
        r'examination\s+slot',
        r'exam\s+slot',
        r'final\s+exam',
        r'midterm\s+exam',
        r'assessment\s+date',
        r'exam\s+timing',
        r'test\s+schedule'
    ]
    
    # Meeting related patterns
    meeting_patterns = [
        r'meeting\s+schedule',
        r'team\s+meet',
        r'zoom\s+call',
        r'google\s+meet',
        r'conference\s+call',
        r'discussion\s+session',
        r'sync\s+up',
        r'catch\s+up',
        r'standup',
        r'meeting\s+link'
    ]
    
    # Check for exam patterns
    for pattern in exam_patterns:
        if re.search(pattern, content):
            return 'exam'
            
    # Check for meeting patterns
    for pattern in meeting_patterns:
        if re.search(pattern, content):
            return 'meeting'
            
    # Default to meeting if contains generic meeting words
    if 'meeting' in content:
        return 'meeting'
    elif 'exam' in content or 'test' in content:
        return 'exam'
        
    return 'event'

def fix_event_types():
    try:
        print("\nAnalyzing emails for event type correction...")
        
        # Find emails with event-related content
        event_emails = emails_collection.find({
            "$or": [
                {"subject": {"$regex": "exam|test|quiz|meeting|schedule|slot", "$options": "i"}},
                {"body": {"$regex": "exam|test|quiz|meeting|schedule|slot", "$options": "i"}}
            ]
        })
        
        total = emails_collection.count_documents({
            "$or": [
                {"subject": {"$regex": "exam|test|quiz|meeting|schedule|slot", "$options": "i"}},
                {"body": {"$regex": "exam|test|quiz|meeting|schedule|slot", "$options": "i"}}
            ]
        })
        
        print(f"Found {total} emails with potential events")
        
        fixed_count = 0
        for i, email in enumerate(event_emails, 1):
            try:
                event_type = determine_event_type(
                    email.get('subject', ''),
                    email.get('body', '')
                )
                
                # Update the event type
                emails_collection.update_one(
                    {'_id': email['_id']},
                    {'$set': {'event_type': event_type}}
                )
                
                fixed_count += 1
                print(f"Updated event type for: {email.get('subject', 'No Subject')}")
                print(f"New event type: {event_type}\n")
                
                if i % 10 == 0:
                    print(f"Processed {i}/{total} emails")
                    
            except Exception as e:
                print(f"Error updating event type for email {email.get('_id')}: {e}")
                continue
        
        print(f"\nEvent Type Fix Results:")
        print(f"Total emails processed: {total}")
        print(f"Successfully updated: {fixed_count}")
        
    except Exception as e:
        print(f"Error during event type fix process: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    fix_event_types() 