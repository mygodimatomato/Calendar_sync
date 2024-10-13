from google.oauth2 import service_account
from googleapiclient.discovery import build
import uuid
import os
import json

# Path to your service account key file (replace with your path)
SERVICE_ACCOUNT_FILE = './calendartracking-438215-49f4ebb4459d.json'

# Define the Google Calendar API scope
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Authenticate using the service account
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

# Build the Google Calendar service
calendar_service = build('calendar', 'v3', credentials=credentials)

# Calendar IDs (replace these with your actual calendar IDs)
source_calendar_ids = [
    'kullonono@gmail.com',  # Personal
    '5t34fcofoehh10ddfuah9c8fpo@group.calendar.google.com', # School Event
    's3nn6t6j7ffv5k4gm4fjnmak9g@group.calendar.google.com', # School Exam
    'ofhv6uij0bphf5nb69qeob43j4@group.calendar.google.com', # School Homework
    '8b9509eae5ef4dc9695d40bb72739427281404e7f44ba97c2df9e7838ddb9f7c@group.calendar.google.com', # School Lab
    '9m12sv5jk0skm9c56ii5m07geo@group.calendar.google.com', # Study Plan
    'e2cgc3g676riqoq68tjt603398@group.calendar.google.com' # Work && Project
]

# Webhook URLs
WEBHOOK_URL_1 = "https://asia-east1-calendartracking-438215.cloudfunctions.net/calendar_api_creation"
WEBHOOK_URL_2 = "https://asia-east1-calendartracking-438215.cloudfunctions.net/calendar_api_deletion"

# File to store channel information to allow stopping them later
CHANNEL_INFO_FILE = './watch_channels.json'

# Function to load channel information from file
def load_channel_info():
    if os.path.exists(CHANNEL_INFO_FILE):
        with open(CHANNEL_INFO_FILE, 'r') as file:
            return json.load(file)
    return {}

# Function to save channel information to file
def save_channel_info(channel_info):
    with open(CHANNEL_INFO_FILE, 'w') as file:
        json.dump(channel_info, file)

# Function to stop an existing watch channel
def stop_channel(channel_id, resource_id):
    try:
        request_body = {
            "id": channel_id,
            "resourceId": resource_id
        }
        calendar_service.channels().stop(body=request_body).execute()
        print(f'Successfully stopped channel {channel_id}')
    except Exception as e:
        print(f'Failed to stop channel {channel_id}: {e}')

# Load existing channel information
channel_info = load_channel_info()

# Set up watch channels for each source calendar
for calendar_id in source_calendar_ids:
    # If there's an existing channel for this calendar, stop both webhook channels if they exist
    if calendar_id in channel_info:
        if 'webhook_1' in channel_info[calendar_id]:
            stop_channel(channel_info[calendar_id]['webhook_1']['channel_id'], channel_info[calendar_id]['webhook_1']['resource_id'])
        if 'webhook_2' in channel_info[calendar_id]:
            stop_channel(channel_info[calendar_id]['webhook_2']['channel_id'], channel_info[calendar_id]['webhook_2']['resource_id'])

    # Generate unique channel IDs using UUID for both webhooks
    channel_id_1 = str(uuid.uuid4())
    channel_id_2 = str(uuid.uuid4())

    # Construct watch requests for both webhook URLs
    request_body_1 = {
        "id": channel_id_1,  # Unique ID for this channel
        "type": "web_hook",
        "address": WEBHOOK_URL_1  # Your Cloud Function endpoint URL for copy_and_modify_events
    }

    request_body_2 = {
        "id": channel_id_2,  # Unique ID for this channel
        "type": "web_hook",
        "address": WEBHOOK_URL_2  # Your Cloud Function endpoint URL for delete_if_original_missing
    }

    # Set up the first watch channel (for copy and modify events)
    try:
        response_1 = calendar_service.events().watch(calendarId=calendar_id, body=request_body_1).execute()
        print(f'Watch channel set up for calendar {calendar_id} with WEBHOOK_URL_1: {response_1}')

        # Save the channel information for webhook 1
        if calendar_id not in channel_info:
            channel_info[calendar_id] = {}
        channel_info[calendar_id]['webhook_1'] = {
            "channel_id": channel_id_1,
            "resource_id": response_1['resourceId']
        }
    except Exception as e:
        print(f'Failed to set up watch channel for calendar {calendar_id} with WEBHOOK_URL_1: {e}')

    # Set up the second watch channel (for deletion check events)
    try:
        response_2 = calendar_service.events().watch(calendarId=calendar_id, body=request_body_2).execute()
        print(f'Watch channel set up for calendar {calendar_id} with WEBHOOK_URL_2: {response_2}')

        # Save the channel information for webhook 2
        channel_info[calendar_id]['webhook_2'] = {
            "channel_id": channel_id_2,
            "resource_id": response_2['resourceId']
        }
    except Exception as e:
        print(f'Failed to set up watch channel for calendar {calendar_id} with WEBHOOK_URL_2: {e}')

# Save updated channel information
save_channel_info(channel_info)
