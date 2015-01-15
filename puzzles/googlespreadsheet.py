import gdata.docs.data
import gdata.docs.client
import gdata.acl.data
import json

_google_config = None

def get_google_config():
    global _google_config
    if _google_config is None:
        _google_config = json.loads(open('/etc/metaphysical/google.json').read())
    return _google_config

def create_google_spreadsheet(title):
    google_config = get_google_config()
    client = gdata.docs.client.DocsClient(source=google_config['source'])
    client.ClientLogin(google_config['username'], google_config['password'], client.source)
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
