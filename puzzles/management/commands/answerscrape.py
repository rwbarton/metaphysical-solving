from django.core.management.base import BaseCommand
from puzzles.models import Puzzle, Status, QueuedAnswer, PuzzleWrongAnswer

import sys
import requests

def submit_url(url):
    puzzle_prefix = 'http://www.20000puzzles.com/puzzle/'
    puzzle_replacement = 'http://www.20000puzzles.com/submit/puzzle/'

    if url.startswith(puzzle_prefix):
        return puzzle_replacement + url[len(puzzle_prefix):]

    if not url.endswith('/'):
        url = url + '/'

    return None

password = open('/etc/puzzle/site-password', 'r').read().rstrip()

solved_status = Status.objects.get(text='solved!')

class Command(BaseCommand):
    help = "Visit call-in pages and update answers in database accordingly"

    def handle(self, *args, **kwargs):
        puzzles = Puzzle.objects.all().order_by('id')
        for puzzle in puzzles:
            if puzzle.status == solved_status:
                continue
            answer_url = submit_url(puzzle.url)
            if answer_url is None:
                continue

            r = requests.get(answer_url, auth=('plant', password))
            if r.status_code != 200:
                print r.text
                sys.exit(1)

            QueuedAnswer.objects.filter(puzzle=puzzle).delete()

            mode = 'none'
            skip = True
            for l in r.text.split('\n'):
                solved_prefix = '      Solved! Answer: <b>'
                solved_suffix = '</b><br>'
                if l.startswith(solved_prefix) and l.endswith(solved_suffix):
                    answer = l[len(solved_prefix):len(l)-len(solved_suffix)]
                    print 'SOLVED ' + puzzle.title + ' = ' + answer
                    puzzle.answer = answer
                    puzzle.status = solved_status
                    puzzle.save()

                if l == '      <h3>In the Queue:</h3>':
                    mode = 'queued'
                if l == '      <h3>Previous Attempts:</h3>':
                    mode = 'wrong'

                non_answer_prefix = '\t  <td>'
                if l.startswith(non_answer_prefix):
                    if skip:    # Every other match is a header which we ignore
                        skip = False
                        continue
                    else:
                        skip = True
                        rest = l[len(non_answer_prefix):]
                        if rest.endswith('</td>'):
                            rest = rest[:-len('</td>')]
                        if mode == 'queued':
                            print 'QUEUED ' + puzzle.title + ' = ' + rest
                            QueuedAnswer.objects.get_or_create(puzzle=puzzle, answer=rest)
                        if mode == 'wrong' and puzzle.status != solved_status:
                            print 'WRONG ' + puzzle.title + ' = ' + rest
                            PuzzleWrongAnswer.objects.get_or_create(puzzle=puzzle, answer=rest)
