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
    new_spreadsheet = client.Create(gdata.docs.data.SPREADSHEET_LABEL, title)
    acl_entry = gdata.docs.data.Acl(
        scope=gdata.acl.data.AclScope(type='default'),
        role=gdata.acl.data.AclWithKey(
            key='with link',
            role=gdata.acl.data.AclRole(value='writer')
            )
        )
    client.Post(acl_entry, new_spreadsheet.GetAclFeedLink().href)
    return new_spreadsheet.GetAlternateLink().href
