from puzzles import puzzlelogin

def submit_answer(submission):
    puzzle = submission.puzzle
    if not puzzle.checkAnswerLink:
        raise ValueError("puzzle %d has no checkAnswerLink" % (puzzle.id,))

    br = puzzlelogin.get_logged_in_browser()
    br.open(puzzle.checkAnswerLink)
    br.select_form(nr=0)
    br['answer'] = submission.answer
    resp = br.submit()

    submission.response = resp.read()
    submission.save()

    if resp.code != 200:
        raise ValueError("answer submission got %d" % (resp.code,))
