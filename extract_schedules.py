from pymongo import MongoClient
from datetime import datetime
import re
from dateutil import parser

# MongoDB setup
client = MongoClient("mongodb://localhost:27017")
db = client.email_dashboard
emails_collection = db.emails
dashboard_schedules = db.dashboard_schedules

def extract_schedule_info(email):
    """Extract schedule information from email content"""
    subject = email.get('subject', '')
    body = email.get('body', '')
    content = f"{subject} {body}".lower()
    
    # Check if it's a schedule-related email
    if not any(word in content for word in [
        'exam', 'test', 'quiz', 'meeting', 'schedule', 'deadline',
        'session', 'class', 'lecture', 'appointment'
    ]):
        return None
    
    # Determine event type
    if any(word in content for word in ['exam', 'test', 'quiz', 'assessment']):
        event_type = 'exam'
    elif any(word in content for word in ['meeting', 'conference', 'discussion']):
        event_type = 'meeting'
    else:
        event_type = 'other'
    
    # Extract time
    time_match = re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))', content)
    time_slot = time_match.group(1) if time_match else None
    
    # Extract meeting link
    link = None
    if event_type == 'meeting':
        link_match = re.search(r'https?://[^\s<>"]+?(?:zoom|meet|teams)\.[^\s<>"]+', content)
        link = link_match.group(0) if link_match else None
    
    # Extract login credentials for exams
    login_id = None
    password = None
    if event_type == 'exam':
        login_match = re.search(r'login\s*(?:id)?:\s*([A-Za-z0-9_-]+)', content, re.IGNORECASE)
        login_id = login_match.group(1) if login_match else None
        
        pwd_match = re.search(r'password:\s*([A-Za-z0-9@#$%^&+=]+)', content, re.IGNORECASE)
        password = pwd_match.group(1) if pwd_match else None
    
    return {
        'id': str(email.get('_id')),
        'title': subject,
        'type': event_type,
        'date': email.get('date'),
        'timeSlot': time_slot,
        'link': link,
        'loginId': login_id,
        'password': password,
        'email_id': email.get('_id')
    }

def process_emails():
    print("Starting schedule extraction...")
    
    # Clear existing schedules
    dashboard_schedules.delete_many({})
    
    # Get all emails
    all_emails = emails_collection.find({})
    total = 0
    found = 0
    
    for email in all_emails:
        total += 1
        schedule = extract_schedule_info(email)
        
        if schedule:
            dashboard_schedules.insert_one(schedule)
            found += 1
            print(f"\nFound event: {schedule['title']}")
            print(f"Type: {schedule['type']}")
            print(f"Date: {schedule['date']}")
            if schedule['timeSlot']:
                print(f"Time: {schedule['timeSlot']}")
    
    print(f"\nProcessing complete:")
    print(f"Total emails processed: {total}")
    print(f"Events found: {found}")

if __name__ == "__main__":
    process_emails() 