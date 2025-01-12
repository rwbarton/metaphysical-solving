from django.core.management.base import BaseCommand
from puzzles.models import Puzzle, Status, QueuedAnswer, PuzzleWrongAnswer

import json
import sys
import time
from datetime import datetime
from urllib.error import HTTPError

from puzzles import puzzlelogin

solved_status = Status.objects.get(text='solved!')

class Command(BaseCommand):
    help = "Visit call-in pages and update answers in database accordingly"

    def handle_wrong_answer(self, puzzle, answer, dry_run=False):
        print('WRONG ' + puzzle.title + ' = ' + answer)
        if not dry_run:
            PuzzleWrongAnswer.objects.get_or_create(puzzle=puzzle, answer=answer)

    def handle_correct_answer(self, puzzle, answer, dry_run=False):
        print('SOLVED ' + puzzle.title + ' = ' + answer)
        if not dry_run:
            puzzle.answer = answer
            puzzle.status = solved_status
            puzzle.save()

    def add_arguments(self, parser):
        parser.add_argument('--file',type=str)
        parser.add_argument('--dry-run',action='store_true')

    def handle(self, *args, **kwargs):
        print("Beginning answerscrape run at " + datetime.now().isoformat())

        if kwargs['file']:
            dict_of_responses = json.load(open(kwargs['file']))

        puzzles = Puzzle.objects.all().order_by('id')
        for puzzle in puzzles:
            if puzzle.answer:   #  answer already in database
                continue

            puzzle_prefix = 'https://puzzles.mit.edu/2011/puzzles/'
            # factory_prefix = 'https://puzzlefactory.place/factory-floor/'
            if puzzle.url.startswith(puzzle_prefix):
                api_url = 'https://interestingthings.museum/api/puzzle/' + \
                             puzzle.url[len(puzzle_prefix):]
            elif puzzle.url.startswith('https://puzzlefactory.place/'):
                api_url = 'https://puzzlefactory.place/api/puzzle/' + \
                             puzzle.url.split('/')[-1]
            else:
                continue

            print(api_url)

            if kwargs['file']:
                try:
                    text = dict_of_responses['api_url']
                except KeyError:
                    print('%s not in provided file'%api_url)
                    continue
            else:
                try:
                    text = puzzlelogin.fetch_with_single_login(api_url)
                except HTTPError as e:
                    if e.code == 404:
                        print(e)
                        continue
                    else:
                        raise
            res = json.loads(text.decode('utf-8'))
            if not kwargs['dry_run']:
                QueuedAnswer.objects.filter(puzzle=puzzle).delete()

            for g in res['guesses']:
                answer = g['guess']
                if g['response'] == 'Incorrect':
                    self.handle_wrong_answer(puzzle, answer, kwargs['dry_run'])
                elif g['response'] == 'Correct!':
                    self.handle_correct_answer(puzzle, answer, kwargs['dry_run'])

            time.sleep(1)

        print("Finished answerscrape run")
