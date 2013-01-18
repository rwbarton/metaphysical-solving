import random
import os
import os.path

from django.http import HttpResponse
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.utils.http import urlencode
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.db import IntegrityError

from models import Status, Priority, Tag, PuzzleWrongAnswer, Puzzle, TagList, UploadedFile, Location, Config, HumbugConfirmation, user_to_email
from forms import UploadForm, AnswerForm
from django.contrib.auth.models import User

def get_motd():
    try:
        return Config.objects.get().motd
    except (Config.DoesNotExist, Config.MultipleObjectsReturned):
        return "Oops, someone broke this message. Please ask an admin to fix it."

def puzzle_context(request, d):
    d1 = dict(d)
    d1['motd'] = get_motd()
    d1['locations'] = Location.objects.all()
    d1['my_puzzles'] = request.user.puzzle_set.order_by('id')
    d1['path'] = request.path
    if 'body' in request.GET:
        d1['body_only'] = True
    d1['humbug_email'] = user_to_email(request.user)
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
            'default_priority': Config.objects.get().default_priority,
            'refresh': 60
            })
    return render_to_response("puzzles/overview.html", context)

@login_required
def overview(request):
    return overview_by(request, Config.objects.get().default_taglist.id)

@login_required
def puzzle(request, puzzle_id):
    return render_to_response("puzzles/puzzle-frames.html", RequestContext(request, {
                'id': puzzle_id,
                'title': Puzzle.objects.get(id=puzzle_id).title
                }))

@login_required
def puzzle_info(request, puzzle_id):
    puzzle = Puzzle.objects.get(id=puzzle_id)
    statuses = Status.objects.all()
    priorities = Priority.objects.all()
    solvers = puzzle.solvers.order_by('first_name', 'last_name')
    you_solving = request.user in solvers
    other_solvers = [solver for solver in solvers if solver != request.user]
    other_users = [other_user
                   for other_user in User.objects.order_by('first_name', 'last_name')
                   if other_user not in solvers
                   and other_user != request.user]
    wrong_answers = puzzle.puzzlewronganswer_set.order_by('-id')
    uploaded_files = puzzle.uploadedfile_set.order_by('id')
    return render_to_response("puzzles/puzzle-info.html", puzzle_context(request, {
                'puzzle': puzzle,
                'statuses': statuses,
                'priorities': priorities,
                'you_solving': you_solving,
                'other_solvers': other_solvers,
                'other_users': other_users,
                'wrong_answers': wrong_answers,
                'uploaded_files': uploaded_files,
                'refresh': 30
                }))

@login_required
def puzzle_spreadsheet(request, puzzle_id):
    spreadsheet = Puzzle.objects.get(id=puzzle_id).spreadsheet
    if spreadsheet:
        return redirect(spreadsheet)
    return HttpResponse("Oops, the spreadsheet isn't ready quite yet. Please wait a moment and then <a href=\"\">refresh</a> this pane.")

@login_required
def puzzle_chat(request, puzzle_id):
    if request.user.userprofile.finished_humbug_registration():
        return redirect("https://p%d.e.plant.humbughq.com/?lurk=p%d" % (int(puzzle_id), int(puzzle_id)))
    else:
        confirmation_url = HumbugConfirmation.objects.get(email=user_to_email(request.user)).confirmation_url
        return render_to_response("puzzles/go-register-for-humbug.html", RequestContext(request, {
                    'confirmation_url': confirmation_url
                    }))

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
def puzzle_logged_chat(request, puzzle_id):
    chat_dir = '/var/www/muc/puzzle-%d' % int(puzzle_id)
    files = os.listdir(chat_dir)
    if files:
        f = max(files)
    else:
        f = '.'
    return redirect('http://metaphysical.no-ip.org/muc/puzzle-%d/%s' % (int(puzzle_id), f))

def handle_puzzle_upload(puzzle, name, file):
    if file.name == '' or file.name[0] == '.' or '/' in file.name:
        raise ValueError
    upload = UploadedFile.objects.create(puzzle=puzzle, name=name)
    directory = os.path.join('/var/www/uploads', str(puzzle.id), str(upload.id))
    os.makedirs(directory)
    outfile = open(os.path.join(directory, file.name), 'wb')
    for chunk in file.chunks():
        outfile.write(chunk)
    outfile.close()
    upload.url = 'http://metaphysicalplant.com/uploads/%d/%d/%s' % (puzzle.id, upload.id, file.name)
    upload.save()

@login_required
def puzzle_upload(request, puzzle_id):
    puzzle = Puzzle.objects.get(id=puzzle_id)
    if request.method == 'POST':
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            handle_puzzle_upload(puzzle, form.cleaned_data['name'], request.FILES['file'])
            return redirect(reverse('puzzles.views.puzzle_info', args=[puzzle_id]))
    else:
        form = UploadForm()
    return render_to_response('puzzles/puzzle-upload.html', puzzle_context(request, {
                'form': form,
                'puzzle': puzzle
                }))

def handle_puzzle_answer(puzzle, answer, result):
    if result == 'correct' or result == 'presumed_correct':
        puzzle.answer = answer
    if result == 'correct':
        puzzle.status = Status.objects.get(css_name='solved')
    puzzle.save()
    if result == 'incorrect':
        try:
            PuzzleWrongAnswer.objects.create(puzzle=puzzle, answer=answer)
        except IntegrityError:
            pass

@login_required
def puzzle_call_in_answer(request, puzzle_id):
    puzzle = Puzzle.objects.get(id=puzzle_id)
    if request.method == 'POST':
        form = AnswerForm(request.POST, request.FILES)
        if form.is_valid():
            handle_puzzle_answer(puzzle, form.cleaned_data['answer'], form.cleaned_data['result'])
            return redirect(reverse('puzzles.views.puzzle_info', args=[puzzle_id]))
    else:
        form = AnswerForm()
    return render_to_response('puzzles/puzzle-call-in-answer.html', puzzle_context(request, {
                'form': form,
                'puzzle': puzzle
                }))

@login_required
def user_location(request):
    location = Location.objects.get(name=request.POST['location'])
    request.user.userprofile.location = location
    request.user.userprofile.save()
    return redirect(request.POST['continue'])

@login_required
def go_to_sleep(request):
    for puzzle in request.user.puzzle_set.all():
        puzzle.solvers.remove(request.user)
        puzzle.save()
    return redirect(request.POST['continue'])

def logout_user(request):
    logout(request)
    return render_to_response('puzzles/logout.html', RequestContext(request))

def logout_return(request):
    return render_to_response('puzzles/logout_return.html', RequestContext(request))

@login_required
def welcome(request):
    return redirect(reverse('puzzles.views.overview'))
