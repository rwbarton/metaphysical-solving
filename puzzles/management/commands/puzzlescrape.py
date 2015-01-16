from django.core.management.base import BaseCommand
import django.db.utils
from puzzles.models import Puzzle, Tag

import requests
from lxml import etree

password = open('/etc/metaphysical/site-password', 'r').read().rstrip()

def create_puzzle(title, url, tag):
    try:
        existing_puzzle = Puzzle.objects.get(title=title, url=url)
    except Puzzle.DoesNotExist:
        try:
            puzzle_object = Puzzle.objects.create(title=title, url=url)
            puzzle_object.tags.add(Tag.objects.get(name=tag))
        except django.db.utils.IntegrityError:
            # puzzle already exists (race)
            pass


class Command(BaseCommand):
    help = "Visit Hunt Overview and create new puzzles"

    def handle(self, *args, **kwargs):
        overview_url = 'http://www.20000puzzles.com/toc.html'

        r = requests.get(overview_url, auth=('plant', password))
        if r.status_code != 200:
            print r.text
            sys.exit(1)

        doc = etree.HTML(r.text)

        puzzles = doc.xpath("//div[@class='form-container nav-related-container']/ul/li/a[1]")
        for puzzle in puzzles:
            title = puzzle.text
            url = puzzle.get('href')
            url = 'http://www.20000puzzles.com' + url + '/'
            rnd = puzzle.getparent().getparent()
            while rnd.tag != 'h2':
                rnd = rnd.getprevious()
            rnd = rnd.text

            print title, url, rnd

            if rnd == 'Machine Room':
                create_puzzle(title=title, url=url, tag='machine room')

            if rnd == 'Optics Lab':
                create_puzzle(title=title, url=url, tag='optics lab')

            if rnd == 'Chemistry Lab':
                create_puzzle(title=title, url=url, tag='chemistry lab')
