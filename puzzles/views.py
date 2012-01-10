import random

from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.utils.http import urlencode
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse

from models import Status, Priority, Tag, Puzzle, TagList, Motd, jabber_username, jabber_password

def get_motd():
    try:
        return Motd.objects.get().motd
    except (Motd.DoesNotExist, Motd.MultipleObjectsReturned):
        return "Oops, someone broke this message. Please ask an admin to fix it."

def puzzle_context(request, d):
    d1 = dict(d)
    d1['motd'] = get_motd()
    return RequestContext(request, d1)

@login_required
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

@login_required
def overview(request):
    try:
        default_taglist_id = TagList.objects.get(name="default").id
    except TagList.DoesNotExist:
        default_taglist_id = TagList.objects.order_by('id')[0].id
    except TagList.DoesNotExist:
        default_taglist_id = 0
    return overview_by(request, default_taglist_id)

@login_required
def puzzle(request, puzzle_id):
    return render_to_response("puzzles/puzzle-frames.html", RequestContext(request, {'id': puzzle_id}))

@login_required
def puzzle_info(request, puzzle_id):
    puzzle = Puzzle.objects.get(id=puzzle_id)
    statuses = Status.objects.all()
    priorities = Priority.objects.all()
    return render_to_response("puzzles/puzzle-info.html", puzzle_context(request, {
                'puzzle': puzzle,
                'statuses': statuses,
                'priorities': priorities
                }))

@login_required
def puzzle_spreadsheet(request, puzzle_id):
    return redirect(Puzzle.objects.get(id=puzzle_id).spreadsheet)

@login_required
def puzzle_chat(request, puzzle_id):
    return redirect("http://metaphysical.no-ip.org/chat/?" +
                    urlencode({'id': puzzle_id,
                               'username': jabber_username(request.user),
                               'password': jabber_password(),
                               'resource': hex(random.getrandbits(64))}))

@login_required
def puzzle_set_status(request, puzzle_id):
    puzzle = Puzzle.objects.get(id=puzzle_id)
    status = Status.objects.get(text=request.POST['status'])
    puzzle.status = status
    puzzle.save()
    return redirect(reverse('puzzles.views.puzzle_info', args=[puzzle_id]))

@login_required
def puzzle_set_priority(request, puzzle_id):
    puzzle = Puzzle.objects.get(id=puzzle_id)
    priority = Priority.objects.get(text=request.POST['priority'])
    puzzle.priority = priority
    puzzle.save()
    return redirect(reverse('puzzles.views.puzzle_info', args=[puzzle_id]))

@login_required
def welcome(request):
    context = puzzle_context(request,{});
    return render_to_response("puzzles/welcome.html",context);
