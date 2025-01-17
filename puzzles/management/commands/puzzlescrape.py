import json

from django.core.management.base import BaseCommand
import django.db.utils
from puzzles.models import Puzzle, Tag, AutoTag, TagList, Status, Round
import re
import json
from bs4 import BeautifulSoup


# from lxml import etree
import urllib.parse
from datetime import datetime

from puzzles import puzzlelogin

base_url = 'https://www.starrats.org'
solved_status = Status.objects.get(text='solved!')


def extract_activity_log_from_file(html_content):
    # Create BeautifulSoup object
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find all script tags
    scripts = soup.find_all('script')

    # Look for the script containing window.initialActivityLog
    for script in scripts:
        if script.string and 'window.initialAllPuzzlesState' in script.string:
            # Extract the array content using regex
            #print(script.string)
            match = re.search(r'window\.initialAllPuzzlesState\s*=\s*(.*?)$',
                            script.string, re.DOTALL)
            if match:
                # Get the JSON string and parse it
                json_str = match.group(1)
                #print(json_str)
                try:
                    return json.loads(json_str)
                    #return None
                except json.JSONDecodeError as e:
                    raise ValueError(f"Failed to parse JSON: {e}")



def create_puzzle(title, url, round_obj, is_meta=False, answer=None, desc=None):
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
            puzzle = Puzzle.objects.create(title=title, url=url, round= round_obj,checkAnswerLink='',
                                           description=desc)
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
        parser.add_argument('--dry-run',action='store_true')
    def handle(self, *args, **kwargs):
        all_puzzles_url = "https://www.two-pi-noir.agency/all_puzzles"

        print("Beginning puzzlescrape run at " + datetime.now().isoformat())

        if kwargs['file']:
            puzzle_list=json.load(open(kwargs['file']))
        else:
            response = puzzlelogin.fetch_with_single_login(all_puzzles_url)
            state = extract_activity_log_from_file(response)
            if kwargs['dry_run']:
                for round in state['rounds']:
#                    round_obj, created = Round.objects.get_or_create(name=puz_round)
                    for puzzle in round['puzzles']:
                        if puzzle['state']=='unlocked':
                            puzzle_answer = puzzle.get('answer',None)
                            puzzle_url = "https://www.two-pi-noir.agency/puzzles/"+puzzle['slug']
                            if puzzle_answer:
                                print(puzzle_answer)
                            else:
                                if not Puzzle.objects.filter(url=puzzle_url).exists():
                                    print("[%s](%s) in %s"%(puzzle_url,puzzle['title'],round['title']))

            else:
                for round in state['rounds']:
                    round_obj, created = Round.objects.get_or_create(name=round['title'])
                    #   if created:
                    #    add_tag_to_taglist(tag_obj, 'Unsolved Rounds')
                    #    add_tag_to_taglist(tag_obj, 'All Rounds')
                    for puzzle in round['puzzles']:
                        if puzzle['state']=='unlocked':
                            puzzle_answer = puzzle.get('answer',None)
                            puzzle_url = "https://www.two-pi-noir.agency/puzzles/"+puzzle['slug']
                            if not Puzzle.objects.filter(url=puzzle_url).exists():
                                print("[%s](%s) in %s" % (puzzle_url, puzzle['title'], round['title']))
                                try:
                                    create_puzzle(puzzle['title'], puzzle_url, round_obj=round_obj,
                                                  desc=puzzle['desc'])
                                except:
                                    continue
                            puzzle_obj = Puzzle.objects.get(url=puzzle_url)
                            if puzzle_answer:
                                puzzle_obj.status = solved_status
                                puzzle_obj.answer = puzzle_answer
                                puzzle_obj.save()



        print("Finished puzzlescrape run")
