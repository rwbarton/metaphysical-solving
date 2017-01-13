from django.core.management.base import BaseCommand
import django.db.utils
from puzzles.models import Puzzle, Tag, AutoTag, TagList

from lxml import etree
import urlparse
from datetime import datetime

from puzzles import puzzlelogin

def create_puzzle(title, url, tag):
    try:
        existing_puzzle = Puzzle.objects.get(title=title, url=url)
    except Puzzle.DoesNotExist:
        # Look for Submit Answer link
        puzzle_page = puzzlelogin.fetch_with_single_login(url)
        doc = etree.HTML(puzzle_page)

        answer_links = doc.xpath("//div[@id='submit']/a[text()='Check answer']")
        if len(answer_links) == 1:
            answer_link = answer_links[0]
            checkAnswerLink = urlparse.urljoin(url, answer_link.get('href'))
        else:
            checkAnswerLink = ''

        try:
            puzzle_object = Puzzle.objects.create(title=title, url=url, checkAnswerLink=checkAnswerLink)
            puzzle_object.tags.add(Tag.objects.get(name=tag))
            print "Created puzzle (%s, %s, %s)" % (title, url, checkAnswerLink)
        except django.db.utils.IntegrityError:
            # puzzle already exists (race)
            pass

def add_tag_to_taglist(tag, taglist_name):
    taglist = TagList.objects.get(name=taglist_name)
    taglist.tags.add(tag)
    taglist.save()

def html_to_tag(html):
    return html.lower()

class Command(BaseCommand):
    help = "Visit Hunt Overview and create new puzzles"

    def handle(self, *args, **kwargs):
        overview_url = 'https://monsters-et-manus.com/puzzle'

        print "Beginning puzzlescrape run at " + datetime.now().isoformat()

        text = puzzlelogin.fetch_with_single_login(overview_url)
        doc = etree.HTML(text)

        puzzles = doc.xpath("//div[@class='puzzle-list-item']/a")
        for puzzle in puzzles:
            title = puzzle.text
            url = puzzle.get('href')
            url = 'https://monsters-et-manus.com' + url
            rnd = puzzle.getparent().getparent().getchildren()[0].getchildren()[0]
            rnd = rnd.text

            try:
                auto_tag = AutoTag.objects.get(html_name=rnd)
                tag = auto_tag.tag
            except AutoTag.DoesNotExist:
                tag, created = Tag.objects.get_or_create(name=html_to_tag(rnd))
                auto_tag, _ = AutoTag.objects.get_or_create(html_name=rnd, tag=tag)
                if created:
                    add_tag_to_taglist(tag, 'unsolved rounds')
                    add_tag_to_taglist(tag, 'all rounds')

            create_puzzle(title=title, url=url, tag=tag)

        print "Finished puzzlescrape run"
