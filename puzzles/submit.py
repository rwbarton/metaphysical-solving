from puzzles import puzzlelogin
# what's a login

import mechanize
import re

def submit_answer(submission, is_request):
    puzzle = submission.puzzle
    check_answer = re.sub('https://molasses.holiday/',
                          'https://molasses.holiday/submit/',
                          puzzle.url)

    br = puzzlelogin.get_logged_in_browser()
    br.open(check_answer)

    if is_request:
        br.select_form(nr=1)
        br['interactionrequest'] = submission.answer
    else:
        br.select_form(nr=0)
        br['submission'] = submission.answer

    resp = br.submit()
    submission.response = resp.read()
    submission.save()

    if resp.code != 200:
        raise ValueError("answer submission got %d" % (resp.code,))
            
