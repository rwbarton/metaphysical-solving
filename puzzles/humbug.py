import mechanize

import models

def humbug_register_email(email):
    br = mechanize.Browser()
    br.set_handle_robots(False)
    br.open("https://plant.humbughq.com/accounts/home/")
    br.select_form(nr=0)
    br["email"] = email
    br.submit()

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
