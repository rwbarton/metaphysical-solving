import os
import sys
import subprocess
import json
import binascii
import zulip
import string
import secrets


from django.conf import settings
from datetime import datetime, timedelta

def zulip_send(user, stream, subject, message):
    if not os.path.exists('configuration/zulip/b+logger.conf'):
        return

    print (user, stream, subject, message)

    client = zulip.Client(config_file="configuration/zulip/b+logger.conf")
    print (client.add_subscriptions(streams=[{"name":stream,},],) )

    client = zulip.Client(config_file="configuration/zulip/%s.conf" % (user,))
    print (client.send_message( { "type": "stream",
                                  "to": stream,
                                  "topic": subject,
                                  "content": message,
                                 } ) )

try:
    zulip_create_settings = json.load(open('configuration/zulip/create.json'))
except IOError:
    zulip_create_settings = None

def zulip_create_user(email, full_name, short_name):
    if zulip_create_settings is None:
        return
    client = zulip.Client(
        email = zulip_create_settings["email"],
        api_key = zulip_create_settings["api_key"],
        site = settings.ZULIP_SERVER_URL)
    random_password = ''.join(secrets.choice(string.ascii_letters) for _ in range(32))
    result = client.create_user(
        {"email":email,
         "full_name":full_name,
         "password": random_password})
        
    return result

def zulip_user_account_active(user):
    try:
        if settings.LIMBO_DISABLED:
            return True
    except AttributeError:
        print("assuming limbo is on!")
        pass
    
    recent_enough = timedelta(days=5)
    client = zulip.Client(config_file="configuration/zulip/b+logger.conf")
    zid = get_user_zulip_id(user)
    if zid>0:
        result = client.get_user_presence(zid)
        try:
            last_update = datetime.fromtimestamp(result["presence"]["aggregated"]["timestamp"])
            return (datetime.now()-last_update) < recent_enough
        except KeyError:
            return False
    return True

from puzzles.models import UserZulipStatus

def get_user_zulip_id(user):
    #client = zulip.Client(config_file="configuration/zulip/b+logger.conf")
    #result = client.call_endpoint(url=f"/users/"+user.email,method="GET",)
    #return result["user"]["user_id"]
    return UserZulipStatus.objects.get(user=user).zulip_id

