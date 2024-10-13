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

# Function to copy events from multiple calendars, modify them, and add to the secondary calendar
def copy_and_modify_events(service, source_calendar_id, target_calendar_id):
    print(f"source_calendar_id: {source_calendar_id}")   
    # Get events from the source calendar
    now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    events_result = service.events().list(calendarId=source_calendar_id, timeMin=now,
                                          maxResults=10, singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])

    for event in events:
        # Create a unique identifier for this event
        unique_identifier = f"{source_calendar_id}-{event['id']}"
        
        # Check if the event is an all-day event
        is_all_day = 'date' in event['start']
        start = event['start']
        end = event['end']
        modified_summary = event['summary']
        modified_description = (event.get('description') or '') + '\nNote: This event was copied to the weekly schedule calendar.'

        # If the event is an all-day event and contains activation time in the summary, convert it to a timed event
        time_match = re.search(r'\((\d{1,2})\.(\d{2})?\s*-\s*(\d{1,2})\.(\d{2})?\)', event['summary'])
        single_time_match = re.search(r'\((\d{1,2})\.(\d{2})?\)', event['summary'])
        # If the event start with "(done)" or "(Done)" or "(cancel)" or "(Cancel)", skip it
        if re.search(r'\(done\)', event['summary'], re.IGNORECASE) or re.search(r'\(cancel\)', event['summary'], re.IGNORECASE):
            continue
        # If the event start with "(" and the second character is not a digit, skip it
        if re.search(r'\([^\d]', event['summary']):
            continue

        if is_all_day and time_match:
            start_hour = int(time_match.group(1))
            start_minute = int(time_match.group(2)) if time_match.group(2) else 0
            end_hour = int(time_match.group(3))
            end_minute = int(time_match.group(4)) if time_match.group(4) else 0
            start_time = datetime.datetime.combine(datetime.datetime.strptime(start['date'], "%Y-%m-%d"), datetime.time(start_hour, start_minute))
            end_time = datetime.datetime.combine(datetime.datetime.strptime(start['date'], "%Y-%m-%d"), datetime.time(end_hour, end_minute))
            start = {'dateTime': start_time.isoformat(), 'timeZone': 'Asia/Taipei'}
            end = {'dateTime': end_time.isoformat(), 'timeZone': 'Asia/Taipei'}
        elif is_all_day and single_time_match:
            start_hour = int(single_time_match.group(1))
            start_minute = int(single_time_match.group(2)) if single_time_match.group(2) else 0
            start_time = datetime.datetime.combine(datetime.datetime.strptime(start['date'], "%Y-%m-%d"), datetime.time(start_hour, start_minute))
            end_time = start_time + datetime.timedelta(minutes=30)
            start = {'dateTime': start_time.isoformat(), 'timeZone': 'Asia/Taipei'}
            end = {'dateTime': end_time.isoformat(), 'timeZone': 'Asia/Taipei'}

        # Check if the event already exists in the target calendar
        target_events_result = service.events().list(calendarId=target_calendar_id, timeMin=now,
                                                     maxResults=50, singleEvents=True,
                                                     orderBy='startTime').execute()
        target_events = target_events_result.get('items', [])
        event_exists = False
        existing_target_event = None

        for target_event in target_events:
            extended_properties = target_event.get('extendedProperties', {}).get('private', {})
            if extended_properties.get('source_event_id') == unique_identifier:
                event_exists = True
                existing_target_event = target_event
                break

        # If the event already exists, check if anything has changed
        if event_exists:
            update_needed = False
            if existing_target_event['summary'] != modified_summary:
                # Update the summary of the existing event
                print(f'Updating summary of existing event: {existing_target_event["summary"]} to {modified_summary}')
                existing_target_event['summary'] = modified_summary
                update_needed = True
            if existing_target_event.get('description') != modified_description:
                # Update the description of the existing event
                print(f'Updating description of existing event: {existing_target_event.get("description")} to {modified_description}')
                existing_target_event['description'] = modified_description
                update_needed = True
            if existing_target_event['start'] != start or existing_target_event['end'] != end:
                # Update the start and end times of the existing event
                print(f'Updating start and end times of existing event: {existing_target_event["start"]} - {existing_target_event["end"]} to {start} - {end}')
                existing_target_event['start'] = start
                existing_target_event['end'] = end
                update_needed = True
            if update_needed:
                updated_event = service.events().update(calendarId=target_calendar_id, eventId=existing_target_event['id'], body=existing_target_event).execute()
                print(f'Updated event: {updated_event.get("htmlLink")}')
            continue

        # Create a new event object with modified details and add extended properties
        new_event = {
            'summary': modified_summary,
            'description': modified_description,
            'start': start,
            'end': end,
            'colorId': event.get('colorId'),  # Retain the same color if available
            'extendedProperties': {
                'private': {
                    'source_event_id': unique_identifier
                }
            }
        }

        # Insert the modified event into the target calendar
        created_event = service.events().insert(calendarId=target_calendar_id, body=new_event).execute()
        print(f'Modified event created in weekly schedule calendar: {created_event.get("htmlLink")}')

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

            # Check if the event status is "cancelled"
            if response.get('status') == 'cancelled':
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
            copy_and_modify_events(service, calendar_id, target_calendar_id)
            # delete_if_original_missing(service, calendar_id, target_calendar_id)
        except IndexError:
            print("Error: Unable to parse calendarId from resourceUri.")
            return ('Unable to parse calendarId', 400)

        return ('', 200)
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return ('Internal server error', 500)