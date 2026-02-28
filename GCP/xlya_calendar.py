import os
import datetime
import requests
from googleapiclient.discovery import build
from groq import Groq
from dotenv import load_dotenv

# ==============================
# LOAD ENV VARIABLES
# ==============================
load_dotenv(dotenv_path=r"C:\Users\Islams Dream\Documents\projects\Xlya-R&D\.env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GCP_API_KEY = os.getenv("GCP_API_KEY")

# Country code → Google public holiday calendar
COUNTRY_HOLIDAY_CALENDAR = {
    "US": "en.usa#holiday@group.v.calendar.google.com",
    "PK": "en.pk#holiday@group.v.calendar.google.com",
    "IN": "en.indian#holiday@group.v.calendar.google.com",
    "GB": "en.uk#holiday@group.v.calendar.google.com",
    # Add more countries here
}


# ==============================
# DETECT USER COUNTRY
# ==============================
def get_user_country():
    """Detect country from public IP, fallback to US."""
    try:
        response = requests.get("https://ipinfo.io/json", timeout=5)
        data = response.json()
        return data.get("country", "US").upper()
    except Exception as e:
        print(f"[IP Geolocation Error]: {e}")
        return "US"


# ==============================
# GET LOCAL DATETIME
# ==============================
def get_local_datetime():
    """Returns local datetime with timezone awareness."""
    return datetime.datetime.now().astimezone()


# ==============================
# GOOGLE CALENDAR CONTEXT
# ==============================
def get_today_holidays():
    """Fetch today’s holidays based on user country."""
    country = get_user_country()
    calendar_id = COUNTRY_HOLIDAY_CALENDAR.get(country, COUNTRY_HOLIDAY_CALENDAR["US"])

    try:
        service = build("calendar", "v3", developerKey=GCP_API_KEY)
        now = get_local_datetime()

        # Start & end of local day
        start_of_day_local = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day_local = now.replace(hour=23, minute=59, second=59, microsecond=999999)

        # Convert to UTC for Google Calendar API
        start_utc = start_of_day_local.astimezone(datetime.timezone.utc).isoformat()
        end_utc = end_of_day_local.astimezone(datetime.timezone.utc).isoformat()

        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=start_utc,
            timeMax=end_utc,
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        events = events_result.get("items", [])
        return [event["summary"] for event in events]

    except Exception as e:
        print(f"[Google Calendar Error]: {e}")
        return []


# ==============================
# GROQ LLM ENGINE
# ==============================
def generate_intelligent_greeting(holidays):
    """Generate a time-aware, human, single-line greeting using Groq."""
    try:
        client = Groq(api_key=GROQ_API_KEY)

        # Determine time-of-day
        now = get_local_datetime()
        hour = now.hour
        if 5 <= hour <= 11:
            time_prefix = "Morning"
        elif 12 <= hour <= 16:
            time_prefix = "Afternoon"
        elif 17 <= hour <= 20:
            time_prefix = "Evening"
        else:
            time_prefix = "Night"

        if holidays:
            holiday_str = ", ".join(holidays)
            user_prompt = (
                f"Event today: {holiday_str}. "
                f"Write ONE short, single-line greeting. "
                f"Human tone. Light rhythm if natural. "
                f"No questions. No explanations. "
                f"Start with '{time_prefix}' if natural. "
                f"Between 6 and 12 words only."
            )
        else:
            user_prompt = (
                f"Write ONE short, single-line {time_prefix.lower()} greeting. "
                f"Human tone. Smooth and natural. "
                f"No questions. No explanations. "
                f"Between 6 and 12 words only."
            )

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Xlya. "
                        "Respond in exactly one short line. "
                        "Never add follow-up sentences."
                    ),
                },
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.75,
            max_completion_tokens=40,
            top_p=0.9,
        )

        response = completion.choices[0].message.content.strip()
        return response.split("\n")[0]

    except Exception as e:
        print(f"[Groq API Error]: {e}")
        return "Have a wonderful day ahead."


# ==============================
# ORCHESTRATOR
# ==============================
def generate_xlya_login_message(user_name="User"):
    holidays = get_today_holidays()
    greeting = generate_intelligent_greeting(holidays)
    return greeting


# ==============================
# ENTRY POINT
# ==============================
if __name__ == "__main__":
    local_time = get_local_datetime()
    country = get_user_country()
    print(local_time)

    response = generate_xlya_login_message(user_name="Alex")
    print(response)
