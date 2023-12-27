import json
from oauth2client.service_account import ServiceAccountCredentials
import httplib2
from googleapiclient import discovery
from django.conf import settings

_google_config = None

def get_google_config():
    global _google_config
    if _google_config is None:
        _google_config = json.loads(open('/etc/puzzle/google.json').read())
    return _google_config


def create_google_spreadsheet(title):
    google_config = get_google_config()
    scopes = ['https://www.googleapis.com/auth/spreadsheets',
              'https://www.googleapis.com/auth/drive.file']
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(google_config, scopes=scopes)
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)
    driveService = discovery.build('drive','v3',credentials=credentials)
    new_spreadsheet = service.spreadsheets().create(
        body={"properties": {"title": title}}).execute()
    if (settings.FOLDER_ID):
        file_id = new_spreadsheet['spreadsheetId']
        file = driveService.files().get(fileId=file_id, fields="parents").execute()
        previous_parents = ",".join(file.get("parents"))    
        driveService.files().update(
            fileId=file_id,
            addParents=settings.FOLDER_ID,
            removeParents=previous_parents,
            fields="id, parents",
        ).execute()
    else:
        acl_entry = {
            'type': 'anyone',
            'role': 'writer',
            'allowFileDiscovery': False
        }
        service = discovery.build('drive', 'v3', http=http)
        service.permissions().create(fileId=new_spreadsheet['spreadsheetId'],
                                body=acl_entry).execute()

    return new_spreadsheet['spreadsheetUrl']

def grant_folder_access(user):
    if (not settings.FOLDER_ID):
        return
    
    google_config = get_google_config()
    scopes = ['https://www.googleapis.com/auth/spreadsheets',
              'https://www.googleapis.com/auth/drive.file']
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(google_config, scopes=scopes)
    http = credentials.authorize(httplib2.Http())
    driveService = discovery.build('drive','v3',credentials=credentials)
    acl_entry = {
        'type': 'user',
        'emailAddress': user,
        'role': 'writer',
    }
    service = discovery.build('drive', 'v3', http=http)
    service.permissions().create(fileId=settings.FOLDER_ID,
                                 body=acl_entry,
                                 sendNotificationEmail=False).execute()

    
