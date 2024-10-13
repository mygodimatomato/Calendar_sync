# Project Name: Calendar_sync

## Description
Calendar_Sync is a Python-based Google Cloud solution for managing Google Calendar events across multiple calendars. This project synchronizes and modifies calendar events across various Google Calendars, providing automation for copying, updating, and deleting calendar entries to ensure consistency. The project also provides webhook notifications to handle changes efficiently.

## Features
- Synchronizes events from multiple Google Calendars to a target calendar.
- Automatically detects and mirrors event changes, including summary and description updates.
- Deletes events from the target calendar if the corresponding source event is deleted.
- Handles specific time parsing for events defined in all-day formats and converts them to timed events.
- Uses Google Cloud Functions to handle webhooks and automate calendar synchronization.

## Project Structure
- **setup_watch_channels.py**: Script for setting up Google Calendar watch channels to receive webhook notifications for updates on the monitored calendars.
- **main.py**: Main Google Cloud Function script to handle incoming webhook requests and perform event synchronization or deletion.
- **requirements.txt**: List of dependencies required to run the Cloud Functions.
- **watch_channels.json**: File used to store information about the created watch channels for managing and renewing them.
- **.gitignore**: File to exclude sensitive information and unnecessary files from being committed to the repository.

## Prerequisites
- Google Cloud Service Account with appropriate permissions to access Google Calendar API
  - Ensure the service account has roles like `roles/editor` or `roles/calendar.admin` to manage calendar events.
- Google Cloud Functions enabled in your Google Cloud Project
- Google Cloud IAM role assigned to allow deploying and invoking Cloud Functions
- Python 3.9 or newer
- Google Cloud SDK installed and configured
- Google Cloud Project with enabled Google Calendar API
- Service account credentials JSON file
- Virtual environment (recommended)

## Installation
1. Clone this repository:
   ```sh
   git clone <repository-url>
   cd CalSyncMaster
   ```

2. Set up a Python virtual environment:
   ```sh
   python3 -m venv Calendar
   source Calendar/bin/activate  # On Windows use `Calendar\Scripts\activate`
   ```

3. Install the required dependencies:
   ```sh
   pip install -r requirements.txt
   ```

## Usage
### Setting Up Watch Channels
1. Update the `setup_watch_channels.py` file with your Google Cloud Project details and calendar IDs.
2. Run the script to set up watch channels:
   ```sh
   python setup_watch_channels.py
   ```

### Deploying Google Cloud Functions

### Requirements for Google Cloud Functions
- Ensure that Google Cloud Functions API is enabled in your Google Cloud Project.
- Service Account must have permissions like `roles/cloudfunctions.developer` and `roles/iam.serviceAccountUser` for deploying and managing Google Cloud Functions.
1. Deploy the function to set up calendar events synchronization:
   ```sh
   gcloud functions deploy setup_watch_channels \
     --runtime python310 \
     --trigger-http \
     --allow-unauthenticated \
     --entry-point setup_watch_channels \
     --region asia-east1
   ```

2. Deploy the function to handle calendar events deletion:
   ```sh
   gcloud functions deploy delete_if_original_missing \
     --runtime python310 \
     --trigger-http \
     --allow-unauthenticated \
     --entry-point delete_if_original_missing \
     --region asia-east1
   ```

### Running the Project
1. Use the `setup_watch_channels.py` script to periodically set up watch channels using Google Cloud Scheduler.
2. The webhook functions will automatically synchronize events or delete them based on changes detected.

## Environment Variables and Security
- Make sure to add your service account JSON file to the `.gitignore` file to keep it safe from being committed.
- The `requirements.txt` file lists all necessary Python libraries that are installed automatically when deploying to Google Cloud.


