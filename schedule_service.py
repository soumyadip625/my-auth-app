import os
from pymongo import MongoClient
from dotenv import load_dotenv
import re
from dateutil import parser
from datetime import datetime

# Load environment variables
load_dotenv()

# MongoDB setup
MONGO_URI = "mongodb://localhost:27017"
client = MongoClient(MONGO_URI)
db = client.email_dashboard
emails_collection = db.emails
schedules_collection = db.schedules

def extract_time_slot(text):
    """Extract time slot from text"""
    try:
        # Common time patterns
        time_patterns = [
            r'(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))\s*(?:to|-)\s*(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))',
            r'(\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm))',
            r'at\s+(\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm))',
            r'time:\s*(\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm))',
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if len(match.groups()) > 1:
                    return f"{match.group(1)} - {match.group(2)}"
                return match.group(1)
                
        return None
    except Exception as e:
        print(f"Error extracting time slot: {e}")
        return None

def extract_meeting_link(text):
    """Extract meeting link from text"""
    try:
        # Meeting link patterns
        link_patterns = [
            r'https?://[^\s<>"]+?(?:zoom|meet|teams|webex)\.[^\s<>"]+',
            r'https?://[^\s<>"]+?(?:zoom|meet|teams|webex)[^\s<>"]*'
        ]
        
        for pattern in link_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return None
    except Exception as e:
        print(f"Error extracting meeting link: {e}")
        return None

def extract_login_info(text):
    """Extract login credentials from text"""
    try:
        # Login patterns
        login_patterns = [
            r'login\s*(?:id)?:\s*([A-Za-z0-9_-]+)',
            r'username:\s*([A-Za-z0-9_-]+)',
            r'user\s*id:\s*([A-Za-z0-9_-]+)',
            r'roll\s*(?:no|number):\s*([A-Za-z0-9_-]+)'
        ]
        
        for pattern in login_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    except Exception as e:
        print(f"Error extracting login info: {e}")
        return None

def extract_password(text):
    """Extract password from text"""
    try:
        # Password patterns
        password_patterns = [
            r'password:\s*([A-Za-z0-9@#$%^&+=]+)',
            r'passcode:\s*([A-Za-z0-9@#$%^&+=]+)',
            r'key:\s*([A-Za-z0-9@#$%^&+=]+)'
        ]
        
        for pattern in password_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    except Exception as e:
        print(f"Error extracting password: {e}")
        return None

def determine_event_type(subject, body):
    """Determine the type of event"""
    content = f"{subject} {body}".lower()
    
    # More specific event type detection
    if any(word in content for word in [
        'exam', 'test', 'quiz', 'assessment', 'examination'
    ]):
        return 'exam'
    elif any(word in content for word in [
        'meeting', 'conference', 'call', 'discussion', 'zoom', 'teams'
    ]):
        return 'meeting'
    elif any(word in content for word in [
        'deadline', 'due date', 'submission'
    ]):
        return 'deadline'
    
    # If no specific type is found but has schedule-related words
    if any(word in content for word in ['schedule', 'appointment', 'event']):
        return 'event'
        
    return 'other'

def is_schedule_related(subject, body):
    """Enhanced check for schedule-related content"""
    content = f"{subject} {body}".lower()
    
    schedule_indicators = [
        # Academic
        'exam schedule', 'test date', 'quiz', 'assignment due',
        'submission deadline', 'class schedule', 'lecture timing',
        
        # Meetings
        'meeting invite', 'conference call', 'zoom meeting',
        'google meet', 'teams meeting', 'discussion scheduled',
        
        # Deadlines
        'deadline', 'due by', 'due date', 'submission by',
        'last date', 'closing date', 'needs to be completed by',
        
        # Events
        'event details', 'workshop', 'seminar', 'webinar',
        'conference', 'training session', 'orientation',
        
        # Time indicators
        'scheduled for', 'will be held', 'timing:', 'at time:',
        'from time:', 'starts at', 'begins at', 'scheduled on',
        
        # Date indicators
        'on date:', 'dated:', 'will take place on',
        'mark your calendar', 'save the date', 'please join us on'
    ]
    
    return any(indicator in content for indicator in schedule_indicators)

def generate_event_title(subject, body, event_type):
    """Generate meaningful event title from content"""
    content = f"{subject} {body}".lower()
    
    # First try to use a clean subject line
    if subject and not subject.lower().startswith('re:'):
        # Remove common prefixes and clean up
        cleaned_subject = re.sub(r'^(?:meeting|invitation|scheduled):\s*', '', subject, flags=re.IGNORECASE)
        if cleaned_subject:
            return cleaned_subject

    # Meeting-specific patterns
    meeting_patterns = [
        r'meeting\s+about\s+([^.\n]+)',
        r'discussion\s+(?:about|regarding|on)\s+([^.\n]+)',
        r'([^.\n]+?)\s+team\s+meeting',
        r'([^.\n]+?)\s+sync(?:\s+up)?\s+meeting',
        r'weekly\s+([^.\n]+?)\s+meeting',
        r'([^.\n]+?)\s+status\s+update',
        r'project\s+([^.\n]+?)\s+discussion',
        r'([^.\n]+?)\s+planning\s+meeting',
        r'sprint\s+([^.\n]+?)\s+meeting'
    ]

    # Try to extract meeting topic
    for pattern in meeting_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            topic = match.group(1).strip()
            return f"Meeting: {topic.title()}"

    # Extract participants if no topic found
    participants_pattern = r'(?:with|between|participants|attendees):\s*([^.\n]+)'
    match = re.search(participants_pattern, content, re.IGNORECASE)
    if match:
        participants = match.group(1).strip()
        return f"Meeting with {participants.title()}"

    # Department/Team detection
    dept_pattern = r'(?:department|team|group):\s*([^.\n]+)'
    match = re.search(dept_pattern, content, re.IGNORECASE)
    if match:
        dept = match.group(1).strip()
        return f"{dept.title()} Team Meeting"

        return subject
        
    content = f"{subject} {body}".lower()
    
    # Title patterns based on event type
    title_patterns = {
        'exam': [
            r'(?:final|midterm|unit)\s+(?:exam|test)\s+(?:for|of)?\s+([^.]+)',
            r'(?:exam|test|quiz)\s+(?:schedule|date)\s+(?:for|of)?\s+([^.]+)',
            r'([^.]+?)\s+(?:exam|test|quiz)\s+(?:schedule|timing)',
        ],
        'meeting': [
            r'(?:meeting|call|discussion)\s+(?:regarding|about|for)\s+([^.]+)',
            r'([^.]+?)\s+(?:team|project|sync)\s+(?:meeting|call)',
            r'(?:weekly|monthly|daily)\s+([^.]+?)\s+(?:meeting|sync)',
        ],
        'deadline': [
            r'(?:deadline|due date)\s+(?:for|of)\s+([^.]+)',
            r'([^.]+?)\s+submission\s+deadline',
            r'([^.]+?)\s+due\s+(?:date|by)',
        ],
        'event': [
            r'(?:invitation|schedule)\s+(?:for|to)\s+([^.]+)',
            r'upcoming\s+([^.]+?)\s+(?:event|session)',
            r'([^.]+?)\s+(?:workshop|seminar|training)',
        ]
    }
    
    # Try to extract meaningful title using patterns
    patterns = title_patterns.get(event_type, [])
    for pattern in patterns:
        match = re.search(pattern, content)
        if match:
            title = match.group(1).strip()
            return f"{event_type.title()}: {title.title()}"
    
    # Fallback titles based on event type
    fallback_titles = {
        'exam': 'Upcoming Examination',
        'meeting': 'Scheduled Meeting',
        'deadline': 'Important Deadline',
        'event': 'Scheduled Event',
        'other': 'Calendar Event'
    }
    
    return fallback_titles.get(event_type, 'Scheduled Event')

def process_stored_emails():
    try:
        print("\nProcessing stored emails for schedules...")
        
        # Use dashboard_schedules collection instead
        dashboard_schedules = db.dashboard_schedules
        dashboard_schedules.delete_many({})
        
        all_emails = emails_collection.find({})
        count = 0
        schedule_count = 0
        
        for email in all_emails:
            try:
                count += 1
                subject = email.get('subject', '')
                body = email.get('body', '')
                
                # Check if email contains schedule information
                event_type = determine_event_type(subject, body)
                if event_type != 'other':  # Only process if it's a specific event type
                    # Extract event details
                    schedule_info = {
                        'id': str(email.get('_id')),
                        'title': subject,
                        'date': email.get('date'),
                        'type': event_type,
                        'timeSlot': extract_time_slot(body),
                        'link': extract_meeting_link(body) if event_type == 'meeting' else None,
                        'loginId': extract_login_info(body) if event_type == 'exam' else None,
                        'password': extract_password(body) if event_type == 'exam' else None
                    }
                    
                    dashboard_schedules.insert_one(schedule_info)
                    schedule_count += 1
                    print(f"\nFound {event_type}: {subject}")
                    print(f"Time: {schedule_info['timeSlot']}")
                    print(f"Date: {schedule_info['date']}")

            except Exception as e:
                print(f"Error processing email {count}: {e}")
                continue

        print(f"\nProcessing complete:")
        print(f"Total emails processed: {count}")
        print(f"Schedules found: {schedule_count}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Starting schedule analysis...")
    process_stored_emails() 