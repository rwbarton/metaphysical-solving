import random

from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.utils.http import urlencode
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse

from models import Status, Priority, Tag, Puzzle, TagList, Config, jabber_username, jabber_password
from django.contrib.auth.models import User

def get_motd():
    try:
        return Config.objects.get().motd
    except (Config.DoesNotExist, Config.MultipleObjectsReturned):
        return "Oops, someone broke this message. Please ask an admin to fix it."

def puzzle_context(request, d):
    d1 = dict(d)
    d1['motd'] = get_motd()
    d1['my_puzzles'] = request.user.puzzle_set.all()
    d1['path'] = request.path
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
    return overview_by(request, Config.objects.get().default_taglist.id)

@login_required
def puzzle(request, puzzle_id):
    return render_to_response("puzzles/puzzle-frames.html", RequestContext(request, {'id': puzzle_id}))

@login_required
def puzzle_info(request, puzzle_id):
    puzzle = Puzzle.objects.get(id=puzzle_id)
    statuses = Status.objects.all()
    priorities = Priority.objects.all()
    solvers = puzzle.solvers.all()
    you_solving = request.user in solvers
    other_solvers = [solver for solver in solvers if solver != request.user]
    other_users = [other_user for other_user in User.objects.all() if other_user not in solvers]
    return render_to_response("puzzles/puzzle-info.html", puzzle_context(request, {
                'puzzle': puzzle,
                'statuses': statuses,
                'priorities': priorities,
                'you_solving': you_solving,
                'other_solvers': other_solvers,
                'other_users': other_users
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
    return redirect(request.POST['continue'])

@login_required
def puzzle_set_priority(request, puzzle_id):
    puzzle = Puzzle.objects.get(id=puzzle_id)
    priority = Priority.objects.get(text=request.POST['priority'])
    puzzle.priority = priority
    puzzle.save()
    return redirect(request.POST['continue'])

@login_required
def puzzle_remove_solver(request, puzzle_id):
    puzzle = Puzzle.objects.get(id=puzzle_id)
    solver = User.objects.get(id=request.POST['solver'])
    puzzle.solvers.remove(solver)
    puzzle.save()
    return redirect(request.POST['continue'])

@login_required
def puzzle_add_solver(request, puzzle_id):
    puzzle = Puzzle.objects.get(id=puzzle_id)
    solver = User.objects.get(id=request.POST['solver'])
    puzzle.solvers.add(solver)
    puzzle.save()
    return redirect(request.POST['continue'])

@login_required
def go_to_sleep(request):
    for puzzle in request.user.puzzle_set.all():
        puzzle.solvers.remove(request.user)
        puzzle.save()
    return redirect(request.POST['continue'])

@login_required
def welcome(request):
    context = puzzle_context(request,{});
    return render_to_response("puzzles/welcome.html",context);
