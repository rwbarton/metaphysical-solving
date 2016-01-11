import requests
import json
from django.conf import settings
from puzzles.models import Puzzle, LacrosseTownCrossword

# returns URL
def create_lacrosse_town_crossword():
    params = {
        "type": "new",
    }
    result = requests.post(
        settings.LACROSSE_TOWN_CROSSWORD_DOMAIN + "/api",
        data={"params": json.dumps(params)})

    result = json.loads(result.text)

    if not result["success"]:
        raise Exception("crossword api did not return success")
    if not result["url"]:
        raise Exception("crossword api did not return a URL")

    return result["url"]

def add_crossword_for_puzzle(puzzle):
    url = create_lacrosse_town_crossword()

    LacrosseTownCrossword.objects.create(
        puzzle=puzzle,
        url=url,
        is_deleted=False)
