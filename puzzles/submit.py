# from puzzles import puzzlelogin
# what's a login

import mechanize

def submit_answer(submission):
    # puzzle = submission.puzzle
    #if not puzzle.checkAnswerLink:
    #    raise ValueError("puzzle %d has no checkAnswerLink" % (puzzle.id,))

    # br = puzzlelogin.get_logged_in_browser()
    # br.open(puzzle.checkAnswerLink)
    br = mechanize.Browser()
    br.open('https://docs.google.com/forms/d/1HeW8fCie61dKbQ_K1hVx9LSXjOzle2gBlJ7vNH_vA34/viewform')
    br.select_form(nr=0)
    control = br.form.find_control('entry.297542697')
    for item in control.items:
        if item.name == "Metaphysical Plant":
            item.selected = True
            br.form['entry.1661589124'] = open('/etc/puzzle/site-password').read().rstrip()
            br.form['entry.1435946593'] = submission.puzzle.title
            br.form['entry.311385330'] = submission.answer
            resp = br.submit()


    submission.response = resp.read()
    submission.save()

    if resp.code != 200:
        raise ValueError("answer submission got %d" % (resp.code,))
