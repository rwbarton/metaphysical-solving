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
    try:
        folder = settings.PUZZLE_FOLDER
        puzzle_template = settings.PUZZLE_TEMPLATE
    except:
        folder = None
        puzzle_template = None

    if (puzzle_template):
        if (folder):
            spreadsheet_file = driveService.files().copy( fileId = puzzle_template,
                                                         body = {"name": title,
                                                                 "parents": [folder],}
                                                         ).execute()
        else:
            spreadsheet_file = driveService.files().copy( fileId = puzzle_template,
                                                         body = {"name": title,}
                                                         ).execute()
        new_spreadsheet = service.spreadsheets().get(
            spreadsheetId=spreadsheet_file['id']).execute()
    else:
        new_spreadsheet = service.spreadsheets().create(
            body={"properties": {"title": title,}}
                  ).execute()
        file_id = new_spreadsheet['spreadsheetId']
        if (folder):
            spreadsheet_file = driveService.files().get(fileId=file_id, fields="parents").execute()
            previous_parents = ",".join(spreadsheet_file.get("parents"))
            driveService.files().update(
                fileId=file_id,
                addParents=folder,
                removeParents=previous_parents,
                fields="id, parents",
            ).execute()
    if (not folder):
        acl_entry = {
            'type': 'anyone',
            'role': 'writer',
            'allowFileDiscovery': False
        }
        driveService.permissions().create(fileId=new_spreadsheet['spreadsheetId'],
                                          body=acl_entry).execute()

    return new_spreadsheet['spreadsheetUrl']

def grant_folder_access(user):
    try:
        folder = settings.PUZZLE_FOLDER
    except:
        folder = None
    if (not folder):
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
    service.permissions().create(fileId=folder,
                                 body=acl_entry,
                                 sendNotificationEmail=False).execute()

    
