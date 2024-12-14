from pymongo import MongoClient
from datetime import datetime

# MongoDB setup
MONGO_URI = "mongodb://localhost:27017"
client = MongoClient(MONGO_URI)
db = client.email_dashboard
attachments_collection = db.pdf_attachments

def clean_duplicate_attachments():
    try:
        print("\nStarting duplicate attachments cleanup...")
        
        # Get total attachments before cleanup
        total_before = attachments_collection.count_documents({})
        print(f"Total attachments before cleanup: {total_before}")
        
        # Find duplicates based on filename
        pipeline = [
            {
                "$group": {
                    "_id": "$filename",
                    "ids": {"$push": "$_id"},
                    "count": {"$sum": 1}
                }
            },
            {
                "$match": {
                    "count": {"$gt": 1}
                }
            }
        ]
        
        duplicates = list(attachments_collection.aggregate(pipeline))
        
        # Remove duplicates keeping only the latest one
        for duplicate in duplicates:
            filename = duplicate['_id']
            # Sort by upload_date and keep the latest
            attachments = list(attachments_collection.find(
                {"filename": filename}
            ).sort("upload_date", -1))
            
            # Keep the first one (latest) and remove others
            for attachment in attachments[1:]:
                attachments_collection.delete_one({"_id": attachment['_id']})
        
        # Get total attachments after cleanup
        total_after = attachments_collection.count_documents({})
        
        print("\nCleanup Summary:")
        print(f"Duplicate attachments removed: {total_before - total_after}")
        print(f"Attachments remaining: {total_after}")

    except Exception as e:
        print(f"Error during cleanup: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    clean_duplicate_attachments() 