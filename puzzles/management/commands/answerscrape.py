from django.core.management.base import BaseCommand
from puzzles.models import Puzzle, Status, QueuedAnswer, PuzzleWrongAnswer

import json
import sys
import time
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
            if puzzle.answer:   #  answer already in database
                continue

            puzzle_prefix = 'https://interestingthings.museum/puzzles/'
            factory_prefix = 'https://puzzlefactory.place/factory-floor/'
            if puzzle.url.startswith(puzzle_prefix):
                api_url = 'https://interestingthings.museum/api/puzzle/' + \
                             puzzle.url[len(puzzle_prefix):]
            elif puzzle.url.startswith(factory_prefix):
                api_url = 'https://puzzlefactory.place/api/puzzle/' + \
                             puzzle.url[len(factory_prefix):]
            else:
                continue

            print(api_url)

            text = puzzlelogin.fetch_with_single_login(api_url)
            res = json.loads(text.decode('utf-8'))

            QueuedAnswer.objects.filter(puzzle=puzzle).delete()

            for g in res['guesses']:
                answer = g['guess']
                if g['response'] == 'Incorrect':
                    self.handle_wrong_answer(puzzle, answer)
                elif g['response'] == 'Correct!':
                    self.handle_correct_answer(puzzle, answer)

            time.sleep(1)

        print("Finished answerscrape run")
