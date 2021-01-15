from django.core.management.base import BaseCommand
from puzzles.models import Puzzle, Status, QueuedAnswer, PuzzleWrongAnswer

import sys
from datetime import datetime

from puzzles import puzzlelogin

solved_status = Status.objects.get(text='solved!')

class Command(BaseCommand):
    help = "Visit call-in pages and update answers in database accordingly"

    def handle_wrong_answer(self, puzzle, answer):
        print('WRONG ' + puzzle.title + ' = ' + answer)
        PuzzleWrongAnswer.objects.get_or_create(puzzle=puzzle, answer=answer)

    def handle_correct_answer(self, puzzle, answer):
        print('SOLVED ' + puzzle.title + ' = ' + answer)
        puzzle.answer = answer
        puzzle.status = solved_status
        puzzle.save()

    def handle(self, *args, **kwargs):
        print("Beginning answerscrape run at " + datetime.now().isoformat())

        puzzles = Puzzle.objects.all().order_by('id')
        for puzzle in puzzles:
            if puzzle.status == solved_status:
                continue

            puzzle_prefix = 'https://perpendicular.institute/puzzle/'
            if puzzle.url.startswith(puzzle_prefix):
                answer_url = 'https://perpendicular.institute/embed/submit/puzzle/' + \
                             puzzle.url[len(puzzle_prefix):]
            else:
                continue

            print(answer_url)

            text = puzzlelogin.fetch_with_single_login(answer_url).decode('utf-8')

            QueuedAnswer.objects.filter(puzzle=puzzle).delete()

            # skip = True
            cur_answer = None
            for l in text.split('\n'):
                answer_prefix = '    <td class="answer">'
                answer_suffix = '</td>'
                if l.startswith(answer_prefix) and l.endswith(answer_suffix):
                    cur_answer = l[len(answer_prefix):len(l)-len(answer_suffix)]

                if l == '    <td>Incorrect</td>':
                    self.handle_wrong_answer(puzzle, cur_answer)

                if l == '    <td style="color: #080; font-weight: bold;">Correct!</td>':
                    self.handle_correct_answer(puzzle, cur_answer)

                # solved_prefix = '      Solved! Answer: <b>'
                # solved_suffix = '</b><br>'
                # if l.startswith(solved_prefix) and l.endswith(solved_suffix):
                #     answer = l[len(solved_prefix):len(l)-len(solved_suffix)]
                #     print 'SOLVED ' + puzzle.title + ' = ' + answer
                #     puzzle.answer = answer
                #     puzzle.status = solved_status
                #     puzzle.save()

                # if l == '      <h3>In the Queue:</h3>':
                #     mode = 'queued'
                # if l == '      <h3>Previous Answers Submitted:</h3>':
                #     mode = 'wrong'

                # non_answer_prefix = '\t  <td>'
                # if l.startswith(non_answer_prefix):
                #     if skip:    # Every other match is a header which we ignore
                #         skip = False
                #         continue
                #     else:
                #         skip = True
                #         rest = l[len(non_answer_prefix):]
                #         if rest.endswith('</td>'):
                #             rest = rest[:-len('</td>')]
                #         if mode == 'queued':
                #             print 'QUEUED ' + puzzle.title + ' = ' + rest
                #             QueuedAnswer.objects.get_or_create(puzzle=puzzle, answer=rest)
                #         if mode == 'wrong' and puzzle.status != solved_status:
                #             print 'WRONG ' + puzzle.title + ' = ' + rest
                #             PuzzleWrongAnswer.objects.get_or_create(puzzle=puzzle, answer=rest)

        print("Finished answerscrape run")
