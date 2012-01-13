import base64
import random
import urllib
from xml.dom.minidom import parse

http_bind_url = 'http://localhost:5280/http-bind/'

def prebind(username, password):
    rid = random.randrange(0, 1000000000)
    resource = "http-prebind-%d" % random.randrange(0, 1000000000)

    dom1 = parse(urllib.urlopen(http_bind_url, "<body rid='%d' xmlns='http://jabber.org/protocol/httpbind' to='metaphysical.no-ip.org' xml:lang='en' wait='60' hold='1' content='text/xml; charset=utf-8' ver='1.6' xmpp:version='1.0' xmlns:xmpp='urn:xmpp:xbosh'/>" % rid))
    rid += 1

    sid = dom1.firstChild.getAttribute('sid')
    authid = dom1.firstChild.getAttribute('authid')
    auth = base64.b64encode("%s\0%s\0%s" % (authid, username, password))

    urllib.urlopen(http_bind_url, "<body rid='%d' xmlns='http://jabber.org/protocol/httpbind' sid='%s'><auth xmlns='urn:ietf:params:xml:ns:xmpp-sasl' mechanism='PLAIN'>%s</auth></body>" % (rid, sid, auth)).read()
    rid += 1

    urllib.urlopen(http_bind_url, "<body rid='%d' xmlns='http://jabber.org/protocol/httpbind' sid='%s' to='metaphysical.no-ip.org' xml:lang='en' xmpp:restart='true' xmlns:xmpp='urn:xmpp:xbosh'/>" % (rid, sid)).read()
    rid += 1

    dom2 = parse(urllib.urlopen(http_bind_url, "<body rid='%d' xmlns='http://jabber.org/protocol/httpbind' sid='%s'><iq type='set' xmlns='jabber:client'><bind xmlns='urn:ietf:params:xml:ns:xmpp-bind'><resource>%s</resource></bind></iq></body>" % (rid, sid, resource)))
    rid += 1

    jid = dom2.getElementsByTagName('jid')[0].childNodes[0].data

    urllib.urlopen(http_bind_url, "<body rid='%d' xmlns='http://jabber.org/protocol/httpbind' sid='%s'><iq type='set' xmlns='jabber:client'><session xmlns='urn:ietf:params:xml:ns:xmpp-session' /></iq></body>" % (rid, sid)).read()
    rid += 1

    return {'rid': rid, 'sid': sid, 'jid': jid}
