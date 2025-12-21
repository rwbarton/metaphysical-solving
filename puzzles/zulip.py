import os
import sys
import subprocess
import json
import binascii
import zulip

from django.conf import settings
from datetime import datetime, timedelta

def zulip_send(user, stream, subject, message):
    if not os.path.exists('/etc/puzzle/zulip/b+logger.conf'):
        return

    print (user, stream, subject, message)

    client = zulip.Client(config_file="/etc/puzzle/zulip/b+logger.conf")
    print (client.add_subscriptions(streams=[{"name":stream,},],) )

    client = zulip.Client(config_file="/etc/puzzle/zulip/%s.conf" % (user,))
    print (client.send_message( { "type": "stream",
                                  "to": stream,
                                  "topic": subject,
                                  "content": message,
                                 } ) )
    #    try:
        # Need to wait for this one to finish so that we know the stream exists (blargh).
#        subprocess.check_call([os.path.join(settings.PROJECT_ROOT,"zulip/api/examples/subscribe"),
#                               "--config-file", "/etc/puzzle/zulip/b+logger.conf",
#                               "--streams", stream])
#        subprocess.Popen([os.path.join(settings.PROJECT_ROOT,"zulip/api/bin/zulip-send"),
#                          "--config-file", "/etc/puzzle/zulip/%s.conf" % (user,),
#                          "--stream", stream, "--subject", subject, "--message", message.encode('utf-8')])
#    except FileNotFoundError:
#        sys.stderr.write('Failed find Zulip API\n')

try:
    zulip_create_settings = json.load(open('/etc/puzzle/zulip/create.json'))
except IOError:
    zulip_create_settings = None

def zulip_create_user(email, full_name, short_name):
    if zulip_create_settings is None:
        return

    try:
        response = subprocess.check_output(
            ['/usr/bin/curl',
             '--insecure',
             '--silent',
             '-X', 'POST',
             '-u', '%s:%s' % (zulip_create_settings['email'], zulip_create_settings['api_key']),
             settings.ZULIP_SERVER_URL + '/api/v1/users',
             '-d', 'email=' + email,
             '-d', 'password=' + binascii.b2a_hex(os.urandom(15)).decode(encoding='ASCII'),
             '-d', b'full_name=' + full_name.encode('utf-8'),
             '-d', b'short_name=' + short_name.encode('utf-8')],
            timeout=5)
        success = (json.loads(response.decode('utf-8')))['result'] == 'success'
    except subprocess.TimeoutExpired:
        response = 'Timed out!\n'
        success = False
    except subprocess.CalledProcessError as err:
        response = '%s returned exit code %d\n'%(err.cmd,err.returncode)
        success = False
        
    if not success:
        sys.stderr.write('Failed to create user (%s, %s, %s): %s' %
                         (email, full_name, short_name, response))

    return success

def zulip_user_account_active(user):
	recent_enough = timedelta(days=5)
	client = zulip.Client(config_file="/etc/puzzle/zulip/b+logger.conf")
	result = client.get_user_presence(user.email)
	try:
		last_update = datetime.fromtimestamp(result["presence"]["aggregated"]["timestamp"])
		if (datetime.now() - last_update) < recent_enough:
			return True
		else:
			return False
	except KeyError:
		return False

	return True
