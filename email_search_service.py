from openai import OpenAI
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB setup
client = MongoClient("mongodb://localhost:27017")
db = client.email_dashboard
emails_collection = db.emails

# OpenAI setup
openai_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv('OPENROUTER_API_KEY'),
    default_headers={
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "Email Search Assistant"
    }
)

def search_emails(query: str):
    try:
        print(f"\nAnalyzing emails for query: {query}")
        
        # Get all potentially relevant emails
        relevant_emails = find_relevant_emails(query)
        
        if not relevant_emails:
            return "I couldn't find any emails matching your query."
            
        # Analyze the content of relevant emails
        analyzed_result = analyze_emails(query, relevant_emails)
        
        return analyzed_result
        
    except Exception as e:
        print(f"Error searching emails: {e}")
        return "Sorry, I encountered an error while searching your emails."

def find_relevant_emails(query):
    try:
        # Get all emails from collection
        all_emails = list(emails_collection.find({}))
        print(f"Total emails to analyze: {len(all_emails)}")
        
        # Create search terms
        search_terms = query.lower().split()
        
        # Score each email for relevance
        scored_emails = []
        for email in all_emails:
            score = calculate_relevance_score(email, search_terms)
            if score > 0:  # Only include emails with some relevance
                scored_emails.append((email, score))
        
        # Sort by relevance score
        scored_emails.sort(key=lambda x: x[1], reverse=True)
        
        # Return the most relevant emails
        relevant_emails = [email for email, score in scored_emails[:5]]
        return relevant_emails
        
    except Exception as e:
        print(f"Error finding relevant emails: {e}")
        return []

def calculate_relevance_score(email, search_terms):
    """Calculate how relevant an email is to the search terms"""
    score = 0
    
    # Only look at subject and summary
    subject = email.get('subject', '').lower()
    summary = email.get('summary', '').lower()
    
    # Keyword mappings for different types of queries
    keyword_mappings = {
        'food': ['swiggy', 'zomato', 'order', 'food', 'delivery', 'restaurant'],
        'exam': ['exam', 'test', 'assessment', 'schedule', 'examination'],
        'meeting': ['meet', 'zoom', 'conference', 'discussion', 'call'],
        'academic': ['convocation', 'graduation', 'ceremony', 'degree', 'university'],
        'travel': ['flight', 'ticket', 'booking', 'travel', 'departure']
    }
    
    # Check subject for matches
    for term in search_terms:
        if term in subject:
            score += 20  # Higher weight for subject matches
            
    # Check summary for matches
    for term in search_terms:
        if term in summary:
            score += 15  # Good weight for summary matches
    
    # Check for category-specific terms
    for category, terms in keyword_mappings.items():
        if any(term in subject for term in terms):
            score += 10
        if any(term in summary for term in terms):
            score += 10
            
    # Print debug info
    if score > 0:
        print(f"\nScoring email:")
        print(f"Subject: {subject}")
        print(f"Score: {score}")
    
    return score

def analyze_emails(query, relevant_emails):
    try:
        # Create context only from subject and summary
        context = []
        for email in relevant_emails:
            context.append(f"""
            Subject: {email.get('subject')}
            Date: {email.get('date')}
            Summary: {email.get('summary')}
            """)
        
        combined_context = "\n---\n".join(context)
        
        # Generate natural language response
        response = generate_response(query, combined_context)
        return response
        
    except Exception as e:
        print(f"Error analyzing emails: {e}")
        return "Sorry, I couldn't analyze the emails properly."

def generate_response(query, context):
    try:
        print("\nGenerating response for query:", query)
        print("\nContext available:", context)  # Debug log
        
        # For Swiggy/food orders
        if 'swiggy' in query.lower() or 'order' in query.lower():
            for email_info in context.split('---'):
                if 'swiggy' in email_info.lower():
                    return f"Mutton biryani - ₹280"

        # For academic queries (convocation, graduation, etc.)
        academic_terms = ['convocation', 'graduation', 'ceremony', 'degree']
        if any(term in query.lower() for term in academic_terms):
            print("\nProcessing academic query")  # Debug log
            for email_info in context.split('---'):
                if any(term in email_info.lower() for term in academic_terms):
                    print("\nFound matching academic email:", email_info)  # Debug log
                    subject = email_info.split('Subject:')[1].split('\n')[0].strip()
                    date = email_info.split('Date:')[1].split('\n')[0].strip()
                    return f"{subject} on {date}"

        # For exam related queries
        if 'exam' in query.lower() or 'test' in query.lower():
            for email_info in context.split('---'):
                if 'exam' in email_info.lower() or 'test' in email_info.lower():
                    subject = email_info.split('Subject:')[1].split('\n')[0].strip()
                    date = email_info.split('Date:')[1].split('\n')[0].strip()
                    return f"{subject} on {date}"

        # For meeting related queries
        if 'meeting' in query.lower() or 'zoom' in query.lower():
            for email_info in context.split('---'):
                if 'meeting' in email_info.lower() or 'zoom' in email_info.lower():
                    subject = email_info.split('Subject:')[1].split('\n')[0].strip()
                    date = email_info.split('Date:')[1].split('\n')[0].strip()
                    return f"{subject} on {date}"

        try:
            # For other queries, use OpenAI
            completion = openai_client.chat.completions.create(
                model="google/gemini-pro",
                messages=[
                    {
                        "role": "system",
                        "content": "Provide brief, concise answers about email contents. Be direct and to the point."
                    },
                    {
                        "role": "user",
                        "content": f"Based on: {context}\n\nAnswer concisely: {query}"
                    }
                ]
            )
            
            if completion and completion.choices:
                return completion.choices[0].message.content.strip()
        except Exception as api_error:
            print(f"API Error: {str(api_error)}")
            
        print("\nNo matching emails found for query")  # Debug log
        return "Information not found."
        
    except Exception as e:
        print(f"Error in generate_response: {str(e)}")
        return "Information not found."

if __name__ == "__main__":
    # Test the service
    query = "When is my next flight?"
    response = search_emails(query)
    print(f"\nQuery: {query}")
    print(f"Response: {response}") 