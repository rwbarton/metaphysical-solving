import gdata.docs.data
import gdata.docs.client
import gdata.acl.data
import json
from oauth2client.service_account import ServiceAccountCredentials


_google_config = None

def get_google_config():
    global _google_config
    if _google_config is None:
        _google_config = json.loads(open('/etc/puzzle/google.json').read())
    return _google_config


def create_google_spreadsheet(title):
    google_config = get_google_config()
    scopes = ['https://spreadsheets.google.com/feeds', 'https://docs.google.com/feeds']
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(google_config, scopes=scopes)
    client = gdata.docs.client.DocsClient(source=google_config['project_id'])
    token = gdata.gauth.OAuth2TokenFromCredentials(credentials)
    token.authorize(client)
    spreadsheet = gdata.docs.data.Resource(gdata.docs.data.SPREADSHEET_LABEL, title)
    new_spreadsheet = client.CreateResource(spreadsheet)
    acl_entry = gdata.docs.data.AclEntry(
        scope=gdata.acl.data.AclScope(type='default'),
        role=gdata.acl.data.AclWithKey(
            key='with link',
            role=gdata.acl.data.AclRole(value='writer')
            )
        )
    client.AddAclEntry(new_spreadsheet, acl_entry)
    return new_spreadsheet.GetAlternateLink().href
