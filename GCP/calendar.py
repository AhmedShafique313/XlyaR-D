import datetime
from googleapiclient.discovery import build
from groq import Groq

# --- CONFIGURATION ---
GROQ_API_KEY = "your_groq_api_key_here"
# Public holiday calendar ID for the US (Change 'usa' for other countries)
HOLIDAY_CALENDAR_ID = "en.usa#holiday@group.v.calendar.google.com"
# A GCP API Key is sufficient for reading public calendars
GCP_API_KEY = "your_gcp_api_key_here"

def get_today_holidays():
    """Fetches any holiday events for today from Google Calendar."""
    try:
        service = build('calendar', 'v3', developerKey=GCP_API_KEY)
        
        # Define the time range for today
        now = datetime.datetime.utcnow()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + 'Z'
        end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999).isoformat() + 'Z'
        
        # List events from the public holiday calendar
        events_result = service.events().list(
            calendarId=HOLIDAY_CALENDAR_ID,
            timeMin=start_of_day,
            timeMax=end_of_day,
            singleEvents=True
        ).execute()
        
        events = events_result.get('items', [])
        return [event['summary'] for event in events]
    except Exception as e:
        print(f"Error fetching from Google Calendar: {e}")
        return []

def generate_intelligent_greeting(holidays, user_name="User"):
    """Uses Groq LLM to generate a personalized greeting based on holidays."""
    client = Groq(api_key=GROQ_API_KEY)
    
    if not holidays:
        prompt = f"Generate a short, friendly morning greeting for {user_name} using the app Xlya."
    else:
        holiday_str = ", ".join(holidays)
        prompt = f"Today is {holiday_str}. Generate a short, intelligent greeting for {user_name} logging into Xlya. Acknowledge the event naturally."

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are Xlya, an intelligent and friendly assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=100
    )
    return completion.choices[0].message.content

# --- EXECUTION ---
if __name__ == "__main__":
    today_events = get_today_holidays()
    greeting = generate_intelligent_greeting(today_events, user_name="Alex")
    print(f"Xlya Response: {greeting}")
