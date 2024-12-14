import imaplib
import email
import os
import json
from datetime import datetime
from email.header import decode_header
import re
from dotenv import load_dotenv
import logging

load_dotenv()

def connect_to_gmail():
    EMAIL = os.getenv('EMAIL')
    PASSWORD = os.getenv('APP_PASSWORD')
    
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL, PASSWORD)
        return mail
    except Exception as e:
        print(f"Error connecting to Gmail: {e}")
        return None

def standardize_date(date_str):
    try:
        # Convert various date formats to standard format
        date_formats = [
            '%d %b %Y',
            '%B %d, %Y',
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%m/%d/%Y'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).strftime('%d %b %Y')
            except:
                continue
                
        return None
    except:
        return None

def extract_bill_info(email_body):
    amount_pattern = r'\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)'
    date_pattern = r'(?:due|payment).+?(?:by|date|on)?\s*(\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}|\d{1,2}[-/]\d{1,2}[-/]\d{4})'
    
    amounts = re.findall(amount_pattern, email_body, re.IGNORECASE)
    dates = re.findall(date_pattern, email_body, re.IGNORECASE)
    
    due_date = None
    if dates:
        # Clean up date string and standardize format
        date_str = dates[0].replace('st', '').replace('nd', '').replace('rd', '').replace('th', '')
        due_date = standardize_date(date_str)
    
    return {
        'amount': float(amounts[0].replace(',', '')) if amounts else None,
        'due_date': due_date
    }

def categorize_bill(subject, body):
    categories = {
        'utility': ['electricity', 'water', 'gas', 'utility', 'utilities'],
        'credit_card': ['credit card', 'card payment', 'card bill'],
        'subscription': ['subscription', 'netflix', 'spotify', 'amazon prime'],
        'internet': ['internet', 'broadband', 'wifi'],
        'phone': ['phone bill', 'mobile bill', 'cellular'],
        'insurance': ['insurance', 'policy payment'],
        'rent': ['rent', 'lease payment', 'housing']
    }
    
    text = (subject + ' ' + body).lower()
    
    for category, keywords in categories.items():
        if any(keyword in text for keyword in keywords):
            return category
    
    return 'other'

def fetch_bills():
    mail = connect_to_gmail()
    if not mail:
        logging.error("Failed to connect to Gmail")
        return []

    bills = []
    
    try:
        # Select the inbox
        mail.select('inbox')
        
        # Search for bill-related emails from last 30 days
        search_criteria = '(OR SUBJECT "bill" SUBJECT "payment" SUBJECT "due") SINCE "30"'
        result, message_numbers = mail.search(None, search_criteria)
        
        if result != 'OK' or not message_numbers[0]:
            logging.warning("No messages found or search failed")
            return []

        for num in message_numbers[0].split():
            try:
                _, msg_data = mail.fetch(num, '(RFC822)')
                if not msg_data or not msg_data[0]:
                    continue

                email_body = msg_data[0][1]
                message = email.message_from_bytes(email_body)
                
                # Get subject safely
                subject_header = message.get("subject")
                if not subject_header:
                    continue
                    
                subject_parts = decode_header(subject_header)[0]
                subject = subject_parts[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(subject_parts[1] or 'utf-8', errors='ignore')
                
                # Get body safely
                body = ""
                if message.is_multipart():
                    for part in message.walk():
                        if part.get_content_type() == "text/plain":
                            try:
                                payload = part.get_payload(decode=True)
                                if payload:
                                    body = payload.decode('utf-8', errors='ignore')
                                break
                            except Exception as e:
                                logging.error(f"Error decoding email part: {e}")
                                continue
                else:
                    try:
                        payload = message.get_payload(decode=True)
                        if payload:
                            body = payload.decode('utf-8', errors='ignore')
                    except Exception as e:
                        logging.error(f"Error decoding email body: {e}")
                        continue

                # Skip if no clear bill indicators
                if not any(word in subject.lower() for word in ['bill', 'payment', 'due']):
                    continue
                
                # Extract bill information
                bill_info = extract_bill_info(body)
                if not bill_info['amount'] or not bill_info['due_date']:
                    continue
                    
                category = categorize_bill(subject, body)
                
                bills.append({
                    'id': num.decode(),
                    'name': subject,
                    'amount': bill_info['amount'],
                    'dueDate': bill_info['due_date'],
                    'category': category,
                    'status': 'pending',
                    'received_date': message['date']
                })
                
            except Exception as e:
                logging.error(f"Error processing email {num}: {e}")
                continue
            
    except Exception as e:
        logging.error(f"Error fetching bills: {e}")
    finally:
        try:
            mail.logout()
        except:
            pass
    
    return bills

if __name__ == "__main__":
    bills = fetch_bills()
    print(f"Found {len(bills)} bills:")
    for bill in bills:
        print(f"\nName: {bill['name']}")
        print(f"Amount: ${bill['amount']}")
        print(f"Due Date: {bill['due_date']}")
        print(f"Category: {bill['category']}") 