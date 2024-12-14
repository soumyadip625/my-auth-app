import schedule
import time
from fetch_bills import fetch_bills
import json
import os
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(
    filename='bill_service.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def update_bills():
    try:
        logging.info("Starting bill update process...")
        
        # Fetch new bills
        new_bills = fetch_bills()
        
        # Read existing bills if file exists
        existing_bills = []
        if os.path.exists('bills_data.json'):
            with open('bills_data.json', 'r') as f:
                existing_bills = json.load(f)
        
        # Merge bills without duplicates
        existing_ids = {bill['id'] for bill in existing_bills}
        unique_new_bills = [bill for bill in new_bills if bill['id'] not in existing_ids]
        
        if unique_new_bills:
            # Add new bills to existing ones
            all_bills = existing_bills + unique_new_bills
            
            # Sort by due date
            all_bills.sort(key=lambda x: datetime.strptime(x['dueDate'], '%d %b %Y'))
            
            # Update status based on due date
            current_date = datetime.now()
            for bill in all_bills:
                due_date = datetime.strptime(bill['dueDate'], '%d %b %Y')
                days_until_due = (due_date - current_date).days
                
                if days_until_due < 0:
                    bill['status'] = 'overdue'
                elif days_until_due <= 7:
                    bill['status'] = 'pending'
                
            # Save updated bills
            with open('bills_data.json', 'w') as f:
                json.dump(all_bills, f, indent=2)
            
            logging.info(f"Added {len(unique_new_bills)} new bills")
        else:
            logging.info("No new bills found")
            
    except Exception as e:
        logging.error(f"Error in bill update process: {e}")

def run_bill_service():
    logging.info("Bill service started")
    
    # Run immediately on start
    update_bills()
    
    # Schedule to run every 5 minutes
    schedule.every(5).minutes.do(update_bills)
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        except Exception as e:
            logging.error(f"Service error: {e}")
            time.sleep(300)  # Wait 5 minutes on error before retrying

if __name__ == "__main__":
    run_bill_service() 