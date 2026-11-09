import json
from googleapiclient import discovery
import google.auth
from puzzles.models import Config
from datetime import datetime

_google_config = None
_adc_config = None

def get_google_config():
    global _google_config
    if _google_config is None:
        _google_config = json.loads(open('configuration/google.json').read())
    return _google_config

def get_adc_config():
    global _adc_config
    if _adc_config is None:
        _adc_config = json.loads(open('configuration/adc.json').read())
    return _adc_config

def get_google_credentials():
    if Config.objects.get().use_adc:
        credentials, _ = google.auth.load_credentials_from_dict(get_adc_config())
    else:
        credentials, _ = google.auth.load_credentials_from_dict(get_google_config())
    return credentials

def create_google_spreadsheet(title,folder=None,puzzle_template=None):
    discovery_url = 'https://sheets.googleapis.com/$discovery/rest?version=v4'
    service = discovery.build('sheets', 'v4', credentials=get_google_credentials(),
                              discoveryServiceUrl=discovery_url)
    drive_service = discovery.build('drive','v3',credentials=get_google_credentials())

    if puzzle_template:
        if folder:
            spreadsheet_file = drive_service.files().copy( fileId = puzzle_template.fid,
                                                         body = {"name": title,
                                                                 "parents": [folder.fid],}
                                                         ).execute()
        else:
            spreadsheet_file = drive_service.files().copy( fileId = puzzle_template.fid,
                                                         body = {"name": title,}
                                                         ).execute()
        new_spreadsheet = service.spreadsheets().get(
            spreadsheetId=spreadsheet_file['id']).execute()
    else:
        new_spreadsheet = service.spreadsheets().create(
            body={"properties": {"title": title,}}
                  ).execute()
        file_id = new_spreadsheet['spreadsheetId']
        if folder:
            spreadsheet_file = drive_service.files().get(fileId=file_id, fields="parents").execute()
            previous_parents = ",".join(spreadsheet_file.get("parents"))
            drive_service.files().update(
                fileId=file_id,
                addParents=folder.fid,
                removeParents=previous_parents,
                fields="id, parents",
            ).execute()
    if not folder:
        acl_entry = {
            'type': 'anyone',
            'role': 'writer',
            'allowFileDiscovery': False
        }
        drive_service.permissions().create(fileId=new_spreadsheet['spreadsheetId'],
                                          body=acl_entry).execute()

    return new_spreadsheet


def grant_access(fid_list,user_list):
    if not fid_list or not user_list:
        return

    ids = []
    service = discovery.build("drive", "v3", credentials=get_google_credentials())

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
    drive_service = discovery.build("drive", "v3", credentials=get_google_credentials())
    metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        }
    folder = drive_service.files().create(body=metadata,fields="id").execute()
    fid = folder.get("id")
    return fid

def get_last_revs(acceptable_puzzles):
  id_list = [{'id':val[0],'fileId':val[1].split('/')[-2]} for val in acceptable_puzzles.values_list('id','spreadsheet')]

  responses = []
  def callback(cb_id, response, exception):
    if exception:
      responses.append((cb_id, None))
    else:
      responses.append((cb_id, max([(datetime.fromisoformat(x['modifiedTime']), x['id']) for x in response["revisions"]])))

  drive_service = discovery.build('drive','v3',credentials=get_google_credentials())
  #TODO: handle more than 100 puzzles (batch size limit)
  batch = drive_service.new_batch_http_request(callback=callback)
  
  for p in id_list:
    batch.add(drive_service.revisions().list(fileId=p['fileId']))
  batch.execute()

  last_updates=[{'puzzle':acceptable_puzzles[int(resp[0])-1],'rev':resp[1]} for resp in responses]
  return sorted(last_updates,key=lambda x: x['rev'][0] if x['rev'] else datetime.now())
    
