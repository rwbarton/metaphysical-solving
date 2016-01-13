# Copy this file to local_settings.py
# and edit it as appropriate for your installation.

# In DEBUG mode, error tracebacks will be served to the browser,
# rather than emailed to the site administrator. Intended for development.
DEBUG = True

# In non-DEBUG mode, you must specify the server names that Django
# is allowed to serve requests for.
#ALLOWED_HOSTS = ['example.com']

# The URL at which your solving server is located. Used to construct
# Zulip messages and uploaded file URLs.
BASE_URL = 'https://example.com'

# Who gets email when the site breaks.
ADMINS = (
    ('Your Name Here', 'somebody@example.com'),
)

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = ''

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    'templates',
)

# Your team name and contact information. Displayed at the top of every page.
# Make sure these are valid HTML!
TEAMNAME = 'AMAZING TEAM'
HQCONTACT = '555-0123 &nbsp;|&nbsp; ateam@example.com'

# Zulip server hostname and URL.
ZULIP_SERVER_HOSTNAME = 'zulip.example.com'
ZULIP_SERVER_URL = 'https://' + ZULIP_SERVER_HOSTNAME

# Zulip URL balancing used to work around browser limits on simultaneous
# connections per server. All the URLs returned by this function should be
# aliases for ZULIP_SERVER_URL.
import random
ZULIP_HOSTNAME_BALANCING = lambda: 'https://e%d.%s' % (
    random.randint(1, 100), ZULIP_SERVER_HOSTNAME)

LACROSSE_TOWN_CROSSWORD_DOMAIN = 'http://enigmatic-mountain-8851.herokuapp.com'
