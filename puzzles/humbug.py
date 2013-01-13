import mechanize

def humbug_register_email(email):
    br = mechanize.Browser()
    br.set_handle_robots(False)
    br.open("https://plant.humbughq.com/accounts/home/")
    br.select_form(nr=0)
    br["email"] = email
    br.submit()
