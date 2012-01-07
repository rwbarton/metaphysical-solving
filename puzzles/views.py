from django.shortcuts import render_to_response
from django.template import RequestContext

from models import Motd

def get_motd():
    try:
        return Motd.objects.get().motd
    except (Motd.DoesNotExist, Motd.MultipleObjectsReturned):
        return "Oops, someone broke this message. Please ask an admin to fix it."

def puzzle_context(request, d):
    d1 = dict(d)
    d1['motd'] = get_motd()
    return RequestContext(request, d1)

def overview(request):
    context = puzzle_context(request, {
            'message': "List of puzzles goes here!",
            })
    return render_to_response("puzzles/overview.html", context)
