from django.shortcuts import render_to_response
from django.template import RequestContext

from models import Tag, Puzzle, TagList, Motd

def get_motd():
    try:
        return Motd.objects.get().motd
    except (Motd.DoesNotExist, Motd.MultipleObjectsReturned):
        return "Oops, someone broke this message. Please ask an admin to fix it."

def puzzle_context(request, d):
    d1 = dict(d)
    d1['motd'] = get_motd()
    return RequestContext(request, d1)

def overview_by(request, taglist_id):
    taglist_id = int(taglist_id)
    taglists = TagList.objects.all()

    tags = TagList.objects.get(id=taglist_id).tags.all()

    context = puzzle_context(request, {
            'taglists': taglists,
            'active_taglist_id': taglist_id,
            'tags': ({
                    'name': tag.name,
                    'puzzles': Tag.objects.get(id=tag.id).puzzle_set.all()
                    }
                     for tag in tags),
            })
    return render_to_response("puzzles/overview.html", context)

def overview(request):
    try:
        default_taglist_id = TagList.objects.get(name="default").id
    except TagList.DoesNotExist:
        default_taglist_id = TagList.objects.order_by('id')[0].id
    except TagList.DoesNotExist:
        default_taglist_id = 0
    return overview_by(request, default_taglist_id)

def puzzle(request, puzzle_id):
    return NotImplementedError

def welcome(request):
    context = puzzle_context(request,{});
    return render_to_response("puzzles/welcome.html",context);
