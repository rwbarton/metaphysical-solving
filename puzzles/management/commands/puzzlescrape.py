import json

from django.core.management.base import BaseCommand
import django.db.utils
from puzzles.models import Puzzle, Tag, AutoTag, TagList, Status, Round

# from lxml import etree
import urllib.parse
from datetime import datetime

from puzzles import puzzlelogin

base_url = 'https://www.starrats.org'
solved_status = Status.objects.get(text='solved!')

def create_puzzle(title, url, round_obj, is_meta=False, answer=None):
    # url = base_url + url
    print(title, url, round, is_meta, answer)

    try:
        puzzle = Puzzle.objects.get(url=url)
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
            puzzle = Puzzle.objects.create(title=title, url=url, round= round_obj,checkAnswerLink='')
            if is_meta:
                puzzle.tags.add(Tag.objects.get(name='meta'))
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
    def add_arguments(self, parser):
        parser.add_argument('--file',type=str)
    def handle(self, *args, **kwargs):
        overview_url = 'https://puzzlefactory.place/api/puzzle_list'

        print("Beginning puzzlescrape run at " + datetime.now().isoformat())

        if kwargs['file']:
            puzzle_list=json.load(open(kwargs['file']))
        else:
            text = puzzlelogin.fetch_with_single_login(overview_url)
            puzzle_list = json.loads(text.decode('utf-8'))
        print(puzzle_list)

        for puz in puzzle_list:
            puz_round = puz['round']
            puz_url = puz['url']
            puz_is_meta = puz['isMeta']

            #puz_round_tag = puz_round.lower()
            round_obj, created = Round.objects.get_or_create(name=puz_round)
            #if created:
            #    add_tag_to_taglist(tag_obj, 'Unsolved Rounds')
            #    add_tag_to_taglist(tag_obj, 'All Rounds')

            create_puzzle(puz['name'], puz_url, round_obj,
                          is_meta=puz_is_meta)

        print("Finished puzzlescrape run")
