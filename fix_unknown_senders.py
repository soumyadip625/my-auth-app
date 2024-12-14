from pymongo import MongoClient
import email.utils
import re

# MongoDB setup
MONGO_URI = "mongodb://localhost:27017"
client = MongoClient(MONGO_URI)
db = client.email_dashboard
emails_collection = db.emails

def extract_sender_name(sender_string):
    """Enhanced sender name extraction"""
    try:
        if not sender_string:
            return 'Unknown Sender'
            
        # Remove extra spaces and newlines
        sender_string = ' '.join(sender_string.split())
        
        # Case 1: Handle "Name <email@domain.com>" format
        if '<' in sender_string and '>' in sender_string:
            name_part = sender_string.split('<')[0].strip()
            if name_part and not name_part.startswith('=?'):
                return name_part.strip('"').strip("'")
                
            # If name part is empty, try to get from email
            email_part = sender_string[sender_string.find('<')+1:sender_string.find('>')]
            if email_part:
                username = email_part.split('@')[0]
                return username.replace('.', ' ').title()
        
        # Case 2: Handle encoded format "=?UTF-8?Q?Name?= <email@domain.com>"
        if '=?' in sender_string and '?=' in sender_string:
            try:
                decoded = email.header.decode_header(sender_string)[0][0]
                if isinstance(decoded, bytes):
                    decoded = decoded.decode()
                if decoded and not all(c in '<>@.' for c in decoded):
                    return decoded.strip()
            except:
                pass
        
        # Case 3: Handle plain email address
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', sender_string)
        if email_match:
            email = email_match.group(0)
            username = email.split('@')[0]
            domain = email.split('@')[1].split('.')[0]
            
            # If username looks like a name
            if not any(c.isdigit() for c in username):
                return username.replace('.', ' ').title()
            # If it's a no-reply or system email
            elif 'noreply' in username.lower() or 'no-reply' in username.lower():
                return f"{domain.title()} Notifications"
            elif 'system' in username.lower() or 'auto' in username.lower():
                return f"{domain.title()} System"
            else:
                return f"{domain.title()} Mail"
        
        # Case 4: Last resort - clean up whatever we have
        cleaned = re.sub(r'[<>@]', ' ', sender_string)
        cleaned = ' '.join(word for word in cleaned.split() if not all(c in '._-0123456789' for c in word))
        if cleaned:
            return cleaned.title()
            
        return 'Unknown Sender'
        
    except Exception as e:
        print(f"Error processing sender: {sender_string} - {str(e)}")
        return 'Unknown Sender'

def fix_unknown_senders():
    try:
        print("\nChecking for emails with unknown senders...")
        
        # Find emails with problematic senders - expanded criteria
        problem_emails = emails_collection.find({
            "$or": [
                {"sender": None},
                {"sender": ""},
                {"sender": "Unknown Sender"},
                {"sender": "unknown"},
                {"sender": {"$regex": "=\\?.*\\?="}},  # Encoded senders
                {"sender": {"$regex": "^[^<]*<.*>$"}}, # Email addresses with brackets
                {"sender": {"$regex": "@"}},           # Raw email addresses
            ]
        })
        
        total = emails_collection.count_documents({
            "$or": [
                {"sender": None},
                {"sender": ""},
                {"sender": "Unknown Sender"},
                {"sender": "unknown"},
                {"sender": {"$regex": "=\\?.*\\?="}},
                {"sender": {"$regex": "^[^<]*<.*>$"}},
                {"sender": {"$regex": "@"}},
            ]
        })
        
        print(f"Found {total} emails needing sender cleanup")
        
        fixed_count = 0
        for i, email in enumerate(problem_emails, 1):
            try:
                original_sender = email.get('sender', '')
                new_sender = extract_sender_name(original_sender)
                
                # Always update if we have a valid sender string
                if new_sender:
                    emails_collection.update_one(
                        {'_id': email['_id']},
                        {'$set': {'sender': new_sender}}
                    )
                    fixed_count += 1
                    print(f"Fixed sender for email: {email.get('subject', 'No Subject')}")
                    print(f"Original sender: {original_sender}")
                    print(f"New sender: {new_sender}\n")
                
                if i % 10 == 0:
                    print(f"Processed {i}/{total} emails")
                    
            except Exception as e:
                print(f"Error fixing sender for email {email.get('_id')}: {e}")
                continue
        
        print(f"\nSender Fix Results:")
        print(f"Total emails processed: {total}")
        print(f"Successfully fixed: {fixed_count}")
        
    except Exception as e:
        print(f"Error during sender fix process: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    fix_unknown_senders() 