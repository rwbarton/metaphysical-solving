from puzzles import puzzlelogin
# what's a login

import mechanize
import re

def submit_answer(submission):
    puzzle = submission.puzzle
    if puzzle.checkAnswerLink:
        check_answer = puzzle.checkAnswerLink
    else:
        return

    br = puzzlelogin.get_logged_in_browser()
    br.open(check_answer)

    br.select_form(nr=0)
    br['answer'] = submission.answer

    resp = br.submit()
    submission.response = resp.read()
    submission.save()

    if resp.code != 200:
        raise ValueError("answer submission got %d" % (resp.code,))

