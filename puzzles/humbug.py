import os
import subprocess
import mechanize

import models
from django.conf import settings

def humbug_register_email(email):
    br = mechanize.Browser()
    br.set_handle_robots(False)
    br.open("https://zulip.com/accounts/home/")
    br.select_form(nr=0)
    br["email"] = email
    resp = br.submit()
    return (resp.get_data().find("You've already registered with this email address. Please log in below.") != -1)

def humbug_registration_finished(email):
    try:
        confirmation_url = models.HumbugConfirmation.objects.get(email=email).confirmation_url
    except models.HumbugConfirmation.DoesNotExist:
        return False            # registration email even hasn't arrived yet, so no chance

    br = mechanize.Browser()
    br.set_handle_robots(False)
    br.open(confirmation_url)
    br.select_form(nr=0)
    resp = br.submit()
    return (resp.get_data().find("You've already registered with this email address. Please log in below.") != -1)


def humbug_send(user, stream, subject, message):
    print (user, stream, subject, message)
    # Need to wait for this one to finish so that we know the stream exists (blargh).
    subprocess.check_call([os.path.join(settings.PROJECT_ROOT,"zulip/api/examples/subscribe"),
                     "--config-file", "/etc/puzzle/zulip/b+logger.conf",
                     "--streams", stream])
    subprocess.Popen([os.path.join(settings.PROJECT_ROOT,"zulip/api/bin/zulip-send"),
                      "--config-file", "/etc/puzzle/zulip/%s.conf" % (user,),
                      "--stream", stream, "--subject", subject, "--message", message])
