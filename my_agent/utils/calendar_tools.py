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
    summary: str = Field(
        ..., # The '...' ellipsis correctly marks this as REQUIRED
        description="The title or summary of the calendar event. This is a required field."
    )
    start_time: str = Field(
        ..., # REQUIRED
        description="The start date and time of the event in ISO 8601 format (e.g., '2025-04-15T10:00:00Z' or '2025-04-15T10:00:00+02:00'). Include the timezone offset or 'Z' for UTC. This is a required field."
    )
    end_time: str = Field(
        ..., # REQUIRED
        description="The end date and time of the event in ISO 8601 format (e.g., '2025-04-15T11:00:00Z' or '2025-04-15T11:00:00+02:00'). Include the timezone offset or 'Z' for UTC. This is a required field."
    )
    description: str = Field(
        default="",
        description="An optional detailed description for the event."
    )
    location: str = Field(
        default="",
        description="An optional location for the event (e.g., 'Conference Room 1' or 'Online')."
    )
    attendees: List[str] = Field(
        default=[],
        description="An optional list of email addresses for attendees to invite."
    )

class CreateCalendarEventTool(BaseTool, BaseGoogleCalendar):
    name: str = "create_calendar_event"
    description: str = (
        "Use this tool to create a new event in the user's Google Calendar. "
        "You MUST provide 'summary', 'start_time', and 'end_time'. "
        "'start_time' and 'end_time' must be in ISO 8601 format (e.g., '2025-04-15T10:00:00Z'). "
        "Ask the user for any missing required information. "
        "IMPORTANT: Format the arguments as a VALID JSON object like this: "
        '{"summary": "Meeting with Team", "start_time": "2025-04-15T09:00:00+02:00", "end_time": "2025-04-15T10:00:00+02:00", "description": "Discuss project", "location": "Room 3", "attendees": ["email@example.com"]}'
    )
    args_schema: type[BaseModel] = CreateCalendarEventInput

    # Adjusted signature: no defaults for required fields defined in args_schema
    def _run(self,
             summary: str,
             start_time: str,
             end_time: str,
             description: str = "",
             location: str = "",
             attendees: Optional[List[str]] = None # Use Optional for clarity
            ) -> Dict[str, Any]:
        """Create a new calendar event based on provided details."""
        try:
            # Ensure service is ready (good practice, already in your code)
            if not self.service:
                 self._authenticate() # Or raise an error if authentication isn't expected here

            # Prepare the event body for the Google API
            # The schema ensures summary, start_time, end_time are present
            event_body = {
                'summary': summary,
                'description': description or "", # Handle potential empty string if default used
                'start': {
                    'dateTime': start_time,
                    # Consider extracting timezone from input or using a default/user setting
                    # For simplicity here, assuming input includes offset or is UTC ('Z')
                    # 'timeZone': 'UTC', # You might need logic to determine the correct timezone
                },
                'end': {
                    'dateTime': end_time,
                    # 'timeZone': 'UTC',
                },
                'location': location or "",
            }

            # Use the provided attendees list if it's not None or empty
            if attendees:
                event_body['attendees'] = [{'email': email} for email in attendees]

            # --- Add simple validation for time format as a fallback ---
            # (Although ideally, the LLM provides it correctly based on description)
            try:
                # Basic check - doesn't fully validate ISO 8601 but catches obvious errors
                datetime.datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                datetime.datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            except ValueError as time_err:
                 return {
                    'status': 'error',
                    'message': f"Invalid time format provided. Expected ISO 8601 format (e.g., 'YYYY-MM-DDTHH:MM:SSZ'). Error: {time_err}",
                    'error_type': 'ValueError'
                 }
            # --- End validation ---


            created_event = self.service.events().insert(
                calendarId='primary',
                body=event_body,
                sendUpdates='all' # Notify attendees
            ).execute()
            print(f"--- Event created successfully: {created_event.get('id')} ---") # Debugging print


            # Format the successful response
            return {
                'status': 'success',
                'message': 'Event created successfully',
                'event': {
                    'id': created_event.get('id'),
                    'summary': created_event.get('summary'),
                    'start': created_event.get('start', {}).get('dateTime'),
                    'end': created_event.get('end', {}).get('dateTime'),
                    'location': created_event.get('location', ''),
                    'description': created_event.get('description', ''),
                    'attendees': [attendee.get('email') for attendee in created_event.get('attendees', [])],
                    'htmlLink': created_event.get('htmlLink') # Link to view event
                }
            }

        except Exception as e:
            # Catch API errors or other issues
            error_message = str(e)
            print(f"--- Error creating event: {error_message} ---") # Debugging print

            # Check for specific Google API error details if possible
            if hasattr(e, 'content'):
                try:
                    error_details = json.loads(e.content.decode('utf-8'))
                    error_message = error_details.get('error', {}).get('message', error_message)
                except:
                    pass # Keep original error message if parsing fails

            return {
                'status': 'error',
                'message': f"Failed to create event: {error_message}",
                'error_type': type(e).__name__
            }

# Create instances of the tools
get_calendar_tool = GetCalendarEventsTool()
create_calendar_tool = CreateCalendarEventTool() 