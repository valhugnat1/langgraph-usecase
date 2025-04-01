from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os.path
import json
import datetime
from typing import List, Dict, Any, Optional
from langchain.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly', 'https://www.googleapis.com/auth/calendar.events']

class BaseGoogleCalendar:
    """Base class for Google Calendar operations with authentication."""
    _creds: Optional[Credentials] = None
    _service: Optional[Any] = None

    def __init__(self):
        self._authenticate()

    def _authenticate(self):
        try:
            creds = None
            if os.path.exists('token.json'):
                creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                    creds = flow.run_local_server(port=0)
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
            
            self._creds = creds
            self._service = build('calendar', 'v3', credentials=self._creds)
            
            # Verify service is properly initialized
            if not self._service:
                raise Exception("Failed to initialize Google Calendar service")
                
        except Exception as e:
            raise Exception(f"Failed to authenticate with Google Calendar: {str(e)}")

    @property
    def service(self):
        """Get the Google Calendar service instance."""
        if not self._service:
            self._authenticate()
        return self._service

    # Remove the problematic _run method from the base class
    # The _run method should only be in the Tool class

class GoogleCalendarInput(BaseModel):
    query: str = Field(default="", description="The query to search for calendar events")
    days_back: int = Field(default=7, description="Number of days to look back for events")

class GetCalendarEventsTool(BaseTool, BaseGoogleCalendar):
    name: str = "get_calendar_events"
    description: str = "Useful for checking your Google Calendar events and schedule"
    args_schema: type[BaseModel] = GoogleCalendarInput

    def _run(self, query: str = "", days_back: int = 7) -> Dict[str, Any]:
        """Run the tool with the given query."""
        try:
            # Ensure we have an authenticated service
            if not self._service:
                self._authenticate()
                
            now = datetime.datetime.utcnow()
            time_min = (now - datetime.timedelta(days=days_back)).isoformat() + 'Z'
            time_max = (now + datetime.timedelta(days=30)).isoformat() + 'Z'
            
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                maxResults=50,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            if not events:
                return {
                    'status': 'success',
                    'message': f'No events found between {time_min} and {time_max}.',
                    'time_range': {
                        'start': time_min,
                        'end': time_max
                    }
                }
            
            formatted_events = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                end = event['end'].get('dateTime', event['end'].get('date'))
                formatted_events.append({
                    'summary': event['summary'],
                    'start': start,
                    'end': end,
                    'location': event.get('location', 'No location specified'),
                    'description': event.get('description', 'No description available'),
                    'organizer': event.get('organizer', {}).get('email', 'Unknown'),
                    'attendees': [attendee.get('email') for attendee in event.get('attendees', [])]
                })
            
            return {
                'status': 'success',
                'message': f'Found {len(formatted_events)} events',
                'time_range': {
                    'start': time_min,
                    'end': time_max
                },
                'events': formatted_events
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'error_type': type(e).__name__
            }
        
class CreateCalendarEventInput(BaseModel):
    summary: str = Field(..., description="Title of the event")
    description: str = Field(default="", description="Description of the event")
    start_time: str = Field(..., description="Start time of the event in ISO format")
    end_time: str = Field(..., description="End time of the event in ISO format")
    location: str = Field(default="", description="Location of the event")
    attendees: List[str] = Field(default=[], description="List of attendee email addresses")

class CreateCalendarEventTool(BaseTool, BaseGoogleCalendar):
    name: str = "create_calendar_event"
    description: str = "Useful for creating new events in your Google Calendar"
    args_schema: type[BaseModel] = CreateCalendarEventInput

    def _run(self, summary: str, description: str = "", start_time: str = "", 
             end_time: str = "", location: str = "", attendees: List[str] = None) -> Dict[str, Any]:
        """Create a new calendar event."""
        try:
            event = {
                'summary': summary,
                'description': description,
                'start': {
                    'dateTime': start_time,
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time,
                    'timeZone': 'UTC',
                },
                'location': location,
            }

            if attendees:
                event['attendees'] = [{'email': email} for email in attendees]

            event = self.service.events().insert(
                calendarId='primary',
                body=event,
                sendUpdates='all'
            ).execute()

            return {
                'status': 'success',
                'message': 'Event created successfully',
                'event': {
                    'id': event['id'],
                    'summary': event['summary'],
                    'start': event['start'],
                    'end': event['end'],
                    'location': event.get('location', ''),
                    'description': event.get('description', ''),
                    'attendees': [attendee.get('email') for attendee in event.get('attendees', [])]
                }
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'error_type': type(e).__name__
            }

# Create instances of the tools
get_calendar_tool = GetCalendarEventsTool()
create_calendar_tool = CreateCalendarEventTool() 