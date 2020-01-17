import os
import sys
import subprocess
import json
import binascii

from django.conf import settings

def zulip_send(user, stream, subject, message):
    if not os.path.exists('/etc/puzzle/zulip/b+logger.conf'):
        return

    print (user, stream, subject, message)
    # Need to wait for this one to finish so that we know the stream exists (blargh).
    subprocess.check_call([os.path.join(settings.PROJECT_ROOT,"zulip/api/examples/subscribe"),
                     "--config-file", "/etc/puzzle/zulip/b+logger.conf",
                     "--streams", stream])
    subprocess.Popen([os.path.join(settings.PROJECT_ROOT,"zulip/api/bin/zulip-send"),
                      "--config-file", "/etc/puzzle/zulip/%s.conf" % (user,),
                      "--stream", stream, "--subject", subject, "--message", message])

try:
    zulip_create_settings = json.load(open('/etc/puzzle/zulip/create.json'))
except IOError:
    zulip_create_settings = None

def zulip_create_user(email, full_name, short_name):
    if zulip_create_settings is None:
        return

    response = subprocess.check_output(
        ['/usr/bin/curl',
         '--silent',
         '-X', 'POST',
         '-u', '%s:%s' % (zulip_create_settings['email'], zulip_create_settings['api_key']),
         settings.ZULIP_SERVER_URL + '/api/v1/users',
         '-d', 'email=' + email,
         '-d', 'password=' + binascii.b2a_hex(os.urandom(15)).decode(encoding='ASCII'),
         '-d', b'full_name=' + full_name.encode('utf-8'),
         '-d', b'short_name=' + short_name.encode('utf-8')])

    success = (json.loads(response.decode('utf-8')))['result'] == 'success'
    if not success:
        sys.stderr.write('Failed to create user (%s, %s, %s): %s' %
                         (email, full_name, short_name, response))

    return success
