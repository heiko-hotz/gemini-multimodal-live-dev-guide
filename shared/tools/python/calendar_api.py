from datetime import datetime, timezone
from google.oauth2 import service_account
from googleapiclient.discovery import build
import google.auth

def get_next_appointment():
    try:
        # Get default credentials
        credentials, project = google.auth.default(
            scopes=['https://www.googleapis.com/auth/calendar.readonly']
        )

        # Build the service
        service = build('calendar', 'v3', credentials=credentials)

        # Get the next event
        now = datetime.now(timezone.utc)  # Current time in UTC with timezone info
        now_str = now.isoformat()  # Already includes Z
        
        # Keep fetching until we find a valid event
        next_event = None
        page_token = None
        while True:
            events_result = service.events().list(
                calendarId='primary',
                timeMin=now_str,
                maxResults=10,  # Fetch more to find valid events
                singleEvents=True,
                orderBy='startTime',
                pageToken=page_token
            ).execute()
            
            # Look for the first valid event (has specific time and title)
            for event in events_result.get('items', []):
                if ('dateTime' in event['start'] and  # This is a timed event, not an all-day event
                    event.get('summary')):  # Event has a title
                    # Parse event time and ensure it's timezone-aware
                    event_time = datetime.fromisoformat(event['start']['dateTime'].replace('Z', '+00:00'))
                    if event_time > now:  # Both are now timezone-aware
                        next_event = event
                        break
            
            if next_event or not events_result.get('nextPageToken'):
                break
            page_token = events_result.get('nextPageToken')

        if not next_event:
            return {'message': 'No upcoming events with time and title found.'}
        
        start_time = next_event['start']['dateTime']  # We know it has dateTime now
        # Format the date and time more nicely
        date_part = start_time.split('T')[0]
        time_part = start_time.split('T')[1].split('+')[0]
        formatted_start = f"{date_part} at {time_part}"

        return {
            'summary': next_event.get('summary', 'No title'),
            'start': formatted_start,
            'location': next_event.get('location', 'No location specified'),
            'description': next_event.get('description', 'No description available')
        }

    except Exception as e:
        raise Exception(f"Failed to get calendar events: {str(e)}") 