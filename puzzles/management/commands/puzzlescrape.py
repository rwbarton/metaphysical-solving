from django.core.management.base import BaseCommand
import django.db.utils
from puzzles.models import Puzzle, Tag

import requests
from lxml import etree

password = open('/etc/metaphysical/site-password', 'r').read().rstrip()

class Command(BaseCommand):
    help = "Visit Hunt Overview and create new puzzles"

    def handle(self, *args, **kwargs):
        overview_url = 'http://www.aliceshrugged.com/overview.html'

        r = requests.get(overview_url, auth=('plant', password))
        if r.status_code != 200:
            print r.text
            sys.exit(1)

        doc = etree.HTML(r.text)

        puzzles = doc.xpath("//div[@id='mh-content']/ul/li/ul/li/ul/li/ul/li/a[1]")
        for puzzle in puzzles:
            title = puzzle.text
            url = puzzle.get('href')
            url = 'http://www.aliceshrugged.com/puzzle/' + url[len('./puzzle/'):]
            rnd = puzzle.getparent().getparent().getparent()[0].text

            # print title, url, rnd
            if rnd == 'The Tea Party':
                try:
                    puzzle_object = Puzzle.objects.create(title=title, url=url)
                    puzzle_object.tags.add(Tag.objects.get(name='tea party'))
                except django.db.utils.IntegrityError:
                    # puzzle already exists
                    pass

            if rnd == 'The White Queen':
                try:
                    puzzle_object = Puzzle.objects.create(title=title, url=url)
                    puzzle_object.tags.add(Tag.objects.get(name='white queen'))
                except django.db.utils.IntegrityError:
                    # puzzle already exists
                    pass

            if rnd == 'The Mock Turtle':
                try:
                    puzzle_object = Puzzle.objects.create(title=title, url=url)
                    puzzle_object.tags.add(Tag.objects.get(name='mock turtle'))
                except django.db.utils.IntegrityError:
                    # puzzle already exists
                    pass

            if rnd == 'The Red and White Knights':
                try:
                    puzzle_object = Puzzle.objects.create(title=title, url=url)
                    puzzle_object.tags.add(Tag.objects.get(name='red and white knights'))
                except django.db.utils.IntegrityError:
                    # puzzle already exists
                    pass

            if rnd == 'The Caucus Race':
                try:
                    puzzle_object = Puzzle.objects.create(title=title, url=url)
                    puzzle_object.tags.add(Tag.objects.get(name='caucus race'))
                except django.db.utils.IntegrityError:
                    # puzzle already exists
                    pass

            if rnd == 'Humpty Dumpty':
                try:
                    puzzle_object = Puzzle.objects.create(title=title, url=url)
                    puzzle_object.tags.add(Tag.objects.get(name='humpty dumpty'))
                except django.db.utils.IntegrityError:
                    # puzzle already exists
                    pass
