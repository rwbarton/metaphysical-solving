import mechanize

config_file = open('/etc/metaphysical/coinheist', 'r')
username = config_file.readline().rstrip()
password = config_file.readline().rstrip()


def submit(puzzle, answer, phone):
    print "Submitting answer %s for puzzle %s (%s)." % (answer, puzzle.title, puzzle.url)

    br = mechanize.Browser()

    # log in
    br.open('http://www.coinheist.com')
    br.select_form(nr=0)
    br['username'] = username
    br['password'] = password
    br.submit()

    # now submit our answer
    answer_url = '%sanswer/' % (puzzle.url,)
    br.open(answer_url)
    br.select_form(nr=0)
    br['req_text'] = answer
    br['contact'] = phone
    resp = br.submit()

    print "Their server said: %s" % (resp.get_data(),)
