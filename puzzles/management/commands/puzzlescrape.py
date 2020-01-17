import json

from django.core.management.base import BaseCommand
import django.db.utils
from puzzles.models import Puzzle, Tag, AutoTag, TagList, Status

from lxml import etree
import urllib.parse
from datetime import datetime

from puzzles import puzzlelogin

solved_status = Status.objects.get(text='solved!')

def create_puzzle(title, url, tag, is_meta=False, answer=None):
    print(title, url, tag, is_meta, answer)

    try:
        puzzle = Puzzle.objects.get(title=title, url=url)
        print('Already exists')
    except Puzzle.DoesNotExist:
        # Look for Submit Answer link
        # puzzle_page = puzzlelogin.fetch_with_single_login(url)
        # doc = etree.HTML(puzzle_page)

        # answer_links = doc.xpath("//div[@id='submit']/a[text()='Check answer']")
        # if len(answer_links) == 1:
        #     answer_link = answer_links[0]
        #     checkAnswerLink = urlparse.urljoin(url, answer_link.get('href'))
        # else:
        #     checkAnswerLink = ''

        print('Adding')

        try:
            puzzle = Puzzle.objects.create(title=title, url=url, checkAnswerLink='')
            puzzle.tags.add(Tag.objects.get(name=tag))
            if is_meta:
                puzzle.tags.add(Tag.objects.get(name='metas'))
            print("Created puzzle (%s, %s)" % (title, url))
        except django.db.utils.IntegrityError:
            # puzzle already exists (race)
            pass

    if answer is not None:
        puzzle.answer = answer
        puzzle.status = solved_status
        puzzle.save()

def add_tag_to_taglist(tag, taglist_name):
    taglist = TagList.objects.get(name=taglist_name)
    taglist.tags.add(tag)
    taglist.save()

def html_to_tag(html):
    return html

class Command(BaseCommand):
    help = "Visit Hunt Overview and create new puzzles"

    def handle(self, *args, **kwargs):
        overview_url = 'https://pennypark.fun/js/puzzles'

        print("Beginning puzzlescrape run at " + datetime.now().isoformat())

        text = puzzlelogin.fetch_with_single_login(overview_url)
        puz = json.loads(text.decode('utf-8'))

        for rnd in puz['lands']:
            rnd_name = rnd['title']

            try:
                auto_tag = AutoTag.objects.get(html_name=rnd_name)
                tag = auto_tag.tag
            except AutoTag.DoesNotExist:
                tag, created = Tag.objects.get_or_create(name=html_to_tag(rnd_name))
                auto_tag, _ = AutoTag.objects.get_or_create(html_name=rnd_name, tag=tag)
                if created:
                    add_tag_to_taglist(tag, 'unsolved rounds')
                    add_tag_to_taglist(tag, 'all rounds')

            # metas are also puzzles
            # create_puzzle(title=title, url=url, tag=tag, is_meta=True)

            for idx, puzzle in enumerate(rnd['puzzles']):
                title = puzzle['title']
                url = puzzle['url']
                url = 'https://pennypark.fun' + url
                answer = puzzle.get('answer')

                create_puzzle(title=title, url=url, tag=tag, is_meta=(idx == 0), answer=answer)

        print("Finished puzzlescrape run")
