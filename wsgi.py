import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'solving.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

path = '/home/puzzle/solving'
if path not in sys.path:
    sys.path.append(path)
