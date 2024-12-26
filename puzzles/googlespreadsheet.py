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


def create_google_spreadsheet(title,folder=None,puzzle_template=None):
    google_config = get_google_config()
    scopes = ['https://www.googleapis.com/auth/spreadsheets',
              'https://www.googleapis.com/auth/drive.file']
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(google_config, scopes=scopes)
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)
    driveService = discovery.build('drive','v3',credentials=credentials)

    if (puzzle_template):
        if (folder):
            spreadsheet_file = driveService.files().copy( fileId = puzzle_template.fid,
                                                         body = {"name": title,
                                                                 "parents": [folder.fid],}
                                                         ).execute()
        else:
            spreadsheet_file = driveService.files().copy( fileId = puzzle_template.fid,
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
                addParents=folder.fid,
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

    return new_spreadsheet


def grant_access(fid_list,user_list):
    if (not fid_list or not user_list):
        return
    
    google_config = get_google_config()
    scopes = ['https://www.googleapis.com/auth/spreadsheets',
              'https://www.googleapis.com/auth/drive.file']
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(google_config, scopes=scopes)
    http = credentials.authorize(httplib2.Http())
    ids = []
    service = discovery.build("drive", "v3", credentials=credentials)

    def callback(request_id, response, exception):
      if exception:
        # Handle error
        print(exception)
      else:
        print(f"Request_Id: {request_id}")
        print(f'Permission Id: {response.get("id")}')
        ids.append(response.get("id"))

    # pylint: disable=maybe-no-member
    batch = service.new_batch_http_request(callback=callback)
    acl_entry = {
        'type': 'user',
        'emailAddress': '',
        'role': 'writer',
    }

    for user in user_list:
        for fid in fid_list:
            batch.add(
                service.permissions().create(fileId=fid,
                                             body={'type':'user',
                                                   'emailAddress':user,
                                                   'role':'writer',},
                                             sendNotificationEmail=False)
            )
    batch.execute()
    
    
def create_google_folder(name):
    google_config = get_google_config()
    scopes = ['https://www.googleapis.com/auth/spreadsheets',
              'https://www.googleapis.com/auth/drive.file']
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(google_config, scopes=scopes)
    http = credentials.authorize(httplib2.Http())
    driveService = discovery.build('drive','v3',credentials=credentials)

    metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        }
    folder = driveService.files().create(body=metadata,fields="id").execute()
    fid = folder.get("id")
    return fid
    
    
