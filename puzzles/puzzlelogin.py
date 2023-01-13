import mechanize


username = open('/etc/puzzle/site-username', 'r').read().rstrip()
password = open('/etc/puzzle/site-password', 'r').read().rstrip()

_br = None

def get_logged_in_browser():
    br = mechanize.Browser()
    br.set_handle_robots(False)
    br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11')]

    r = br.open('https://interestingthings.museum/login')

    br.select_form(nr=0)
    br['username'] = username
    br['password'] = password
    br.submit()

    r = br.open('https://puzzlefactory.place/login')

    br.select_form(nr=0)
    br['username'] = username
    br['password'] = password
    br.submit()

    return br

# Use this in scripts that run for a short time
# but fetch a lot of pages.
def fetch_with_single_login(url):
    global _br

    if _br is None:
        _br = get_logged_in_browser()

    r = _br.open(url)
    if r.code != 200:
        print(r.read())
        sys.exit(1)

    return r.read()
