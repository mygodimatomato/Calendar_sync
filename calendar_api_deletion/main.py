from google.oauth2 import service_account
from googleapiclient.discovery import build
import datetime
import re

# Assuming you have already set up credentials and services for Google Calendar API
SERVICE_ACCOUNT_FILE = './calendartracking-438215-49f4ebb4459d.json'
SCOPES = ['https://www.googleapis.com/auth/calendar']
credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

target_calendar_id = '21587845ff29c3a53a52df020c795bdb1c261d8b3dbd6adff238d16d298c6430@group.calendar.google.com'  # The target calendar

source_calendar_ids = [
    'kullonono@gmail.com',  # Personal
    '5t34fcofoehh10ddfuah9c8fpo@group.calendar.google.com', # School Event
    's3nn6t6j7ffv5k4gm4fjnmak9g@group.calendar.google.com', # School Exam
    'ofhv6uij0bphf5nb69qeob43j4@group.calendar.google.com', # School Homework
    '8b9509eae5ef4dc9695d40bb72739427281404e7f44ba97c2df9e7838ddb9f7c@group.calendar.google.com', # School Lab
    '9m12sv5jk0skm9c56ii5m07geo@group.calendar.google.com', # Study Plan
    'e2cgc3g676riqoq68tjt603398@group.calendar.google.com' # Work && Project
]

# Build the Google Calendar service
service = build('calendar', 'v3', credentials=credentials)

# Function to check if the original event still exists, and delete the copied event if it doesn't
def delete_if_original_missing(service, source_calendar_id, target_calendar_id):
    # print("start delete_if_original_missing")
    # Get events from the target calendar
    now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    target_events_result = service.events().list(calendarId=target_calendar_id, timeMin=now,
                                                 maxResults=50, singleEvents=True,
                                                 orderBy='startTime').execute()
    target_events = target_events_result.get('items', [])

    for target_event in target_events:
        # print(f"checking target_event: {target_event['summary']}")
        # Check if the event has extended properties indicating it was copied
        extended_properties = target_event.get('extendedProperties', {}).get('private', {})
        source_event_id = extended_properties.get('source_event_id')
        if not source_event_id:
            continue

        # Extract the source calendar ID and event ID from the source_event_id
        try:
            source_calendar_id, original_event_id = source_event_id.split('-', 1)
        except ValueError:
            print(f"Error parsing source_event_id: {source_event_id}")
            continue

        # Check if the original event still exists
        try:
            response = service.events().get(calendarId=source_calendar_id, eventId=original_event_id).execute()
            # print(f"Original event found: {response}")  # Print the response to debug

            # Check if the event status is "cancelled" or if the event summary contains "(cancel)" or "(Cancel)"
            if response.get('status') == 'cancelled' or re.search(r'\(cancel\)', response.get('summary'), re.IGNORECASE):
                print(f"Original event is cancelled, deleting copied event: {target_event['summary']}")
                service.events().delete(calendarId=target_calendar_id, eventId=target_event['id']).execute()
        except Exception as e:
            print(f"Error fetching original event: {str(e)}")

def main(request):
    """HTTP Cloud Function that processes incoming calendar webhook requests."""
    try:
        # Extract and log request headers
        headers = request.headers
        # print(f"Request headers: {headers}")

        # Extract resource information from headers
        resource_uri = headers.get('X-Goog-Resource-Uri')
        resource_id = headers.get('X-Goog-Resource-Id')

        if not resource_uri or not resource_id:
            print("Error: Missing resourceUri or resourceId in headers.")
            return ('Missing resourceUri or resourceId', 400)

        # Extract calendarId from the resource_uri
        # The calendarId will be after the 'calendars/' part of the URI, e.g.,
        # https://www.googleapis.com/calendar/v3/calendars/kullonono%40gmail.com/events
        try:
            calendar_id = resource_uri.split('/calendars/')[1].split('/')[0]
            calendar_id = calendar_id.replace('%40', '@')  # Handle URL encoding for '@'
            # print(f"calendar_id: {calendar_id}")
            delete_if_original_missing(service, calendar_id, target_calendar_id)
        except IndexError:
            print("Error: Unable to parse calendarId from resourceUri.")
            return ('Unable to parse calendarId', 400)

        return ('', 200)
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return ('Internal server error', 500)