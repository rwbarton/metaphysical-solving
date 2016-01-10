import os
import subprocess

from django.conf import settings

def zulip_send(user, stream, subject, message):
    print (user, stream, subject, message)
    # Need to wait for this one to finish so that we know the stream exists (blargh).
    subprocess.check_call([os.path.join(settings.PROJECT_ROOT,"zulip/api/examples/subscribe"),
                     "--config-file", "/etc/puzzle/zulip/b+logger.conf",
                     "--streams", stream])
    subprocess.Popen([os.path.join(settings.PROJECT_ROOT,"zulip/api/bin/zulip-send"),
                      "--config-file", "/etc/puzzle/zulip/%s.conf" % (user,),
                      "--stream", stream, "--subject", subject, "--message", message])
