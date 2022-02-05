import random
import os
import os.path
import urllib
import json
import re

from collections import defaultdict

from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template import RequestContext
from django.utils.http import urlencode
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.db import IntegrityError
from django import forms

from puzzles.models import Status, Priority, Tag, QueuedAnswer, SubmittedAnswer, \
    PuzzleWrongAnswer, Puzzle, TagList, UploadedFile, Location, Config
from puzzles.forms import UploadForm, AnswerForm
from puzzles.submit import submit_answer
from puzzles.zulip import zulip_send
from django.contrib.auth.models import User
from django.conf import settings

def get_motd():
    try:
        return Config.objects.get().motd
    except (Config.DoesNotExist, Config.MultipleObjectsReturned):
        return "Oops, someone broke this message. Please ask an admin to fix it."

def get_jitsi_data():
    try:
        room_list_json = urllib.request.urlopen(settings.JITSI_ROOMS_URL, timeout = 5)
        room_list_object = json.loads(room_list_json.read().decode('utf-8'))
        room_list = room_list_object["room_census"]
        user_dict = defaultdict(list)
        for room in room_list:
            for user in room["participants"]:
                roomUrl = re.sub(r'[[](\w*)[]]',r'\1/',room["room_name"].split("@")[0])
                try:
                    roomId = room["room_name"].split("-")[1]
                    roomTitle = Puzzle.objects.select_related().get(id=roomId).title
                    puzzleUrl = Puzzle.objects.select_related().get(id=roomId).url
                except:
                    roomTitle = roomUrl
                    roomId = None
                user_dict[user].append((roomUrl,roomTitle,roomId))
        user_list = sorted(user_dict.items())
    except:
        user_list = None
    return user_list

def puzzle_context(request, d):
    d1 = dict(d)
    d1['teamname'] = settings.TEAMNAME
    d1['motd'] = get_motd()
    d1['hqcontact'] = settings.HQCONTACT
    d1['locations'] = Location.objects.all()
    d1['my_puzzles'] = request.user.puzzle_set.order_by('id')
    d1['path'] = request.path
    if 'body' in request.GET:
        d1['body_only'] = True
    return d1

@login_required
def overview_by(request, taglist_id):
    taglist_id = int(taglist_id)
    taglists = TagList.objects.all()

    tags = TagList.objects.get(id=taglist_id).tags.all()

    assigned_puzzles = {}
    unassigned_only = TagList.objects.get(id=taglist_id).name == 'unassigned'
    if unassigned_only:
        assigned_tags = TagList.objects.get(name='assigned').tags.all()
        for atag in assigned_tags:
            puzzles = atag.puzzle_set.select_related().all()
            for p in puzzles:
                assigned_puzzles[p.id] = True

    context = puzzle_context(request, {
            'taglists': taglists,
            'active_taglist_id': taglist_id,
            'tags': ({
                    'name': tag.name,
                    'puzzles': Tag.objects.get(id=tag.id).puzzle_set.select_related().all()
                    }
                     for tag in tags),
            'assigned_puzzles': assigned_puzzles,
            'jitsi_data': get_jitsi_data(),
            'unassigned_only': unassigned_only,
            'default_priority': Config.objects.get().default_priority,
            'refresh': 120
            })
    return render(request, "puzzles/overview.html", context=context)

@login_required
def overview(request):
    return overview_by(request, Config.objects.get().default_taglist.id)

@login_required
def puzzle(request, puzzle_id):
    return render(request, "puzzles/puzzle-frames.html", context={
                'id': puzzle_id,
                'title': Puzzle.objects.get(id=puzzle_id).title
                })

@login_required
def puzzle_info(request, puzzle_id):
    puzzle = Puzzle.objects.select_related().get(id=puzzle_id)
    statuses = Status.objects.all()
    priorities = Priority.objects.all()
    solvers = puzzle.solvers.order_by('first_name', 'last_name')
    you_solving = request.user in solvers
    other_solvers = [solver for solver in solvers if solver != request.user]
    other_users = [other_user
                   for other_user in User.objects.order_by('first_name', 'last_name')
                   if other_user not in solvers
                   and other_user != request.user]
    queued_answers = puzzle.queuedanswer_set.order_by('-id')
    wrong_answers = puzzle.puzzlewronganswer_set.order_by('-id')
    uploaded_files = puzzle.uploadedfile_set.order_by('id')
    return render(request, "puzzles/puzzle-info.html", context=puzzle_context(request, {
                'puzzle': puzzle,
                'statuses': statuses,
                'priorities': priorities,
                'you_solving': you_solving,
                'other_solvers': other_solvers,
                'other_users': other_users,
                'queued_answers': queued_answers,
                'wrong_answers': wrong_answers,
                'uploaded_files': uploaded_files,
                'answer_callin': settings.ANSWER_CALLIN_ENABLED, # and puzzle.checkAnswerLink,
                'jitsi_room_id': puzzle.jitsi_room_id(),
                'refresh': 60
                }))

@login_required
def puzzle_spreadsheet(request, puzzle_id):
    spreadsheet = Puzzle.objects.get(id=puzzle_id).spreadsheet
    if spreadsheet:
        return redirect(spreadsheet)
    return HttpResponse("Oops, the spreadsheet isn't ready quite yet. Please wait a moment and then <a href=\"\">refresh</a> this pane.")

@login_required
def puzzle_chat(request, puzzle_id):
    return redirect("%s/?stream=p%d#all_messages" % (settings.ZULIP_SERVER_URL,int(puzzle_id)))

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
    upload.url = '%s/uploads/%d/%d/%s' % (settings.BASE_URL, puzzle.id, upload.id, file.name)
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
    return render(request, 'puzzles/puzzle-upload.html', context=puzzle_context(request, {
                'form': form,
                'puzzle': puzzle
                }))

def handle_puzzle_answer(puzzle, user, answer, backsolved, phone, request):
    QueuedAnswer.objects.get_or_create(puzzle=puzzle, answer=answer)
    submission = SubmittedAnswer.objects.create(
        puzzle=puzzle, user=user, answer=answer,
        backsolved=backsolved, phone=phone)
    submit_answer(submission, request)
    submission.success = True
    submission.save()
    zulip_send('b+status', puzzle.zulip_stream(), 'Calling in...',
               ':telephone: %s %s called in %s' %
               (user.first_name, user.last_name, answer))

@login_required
def answer_submit_result(request, answer_id, result):
    queued_answer = QueuedAnswer.objects.get(id=answer_id)
    handle_puzzle_answer_result(queued_answer.puzzle, queued_answer.answer, result)
    queued_answer.delete()
    return redirect(reverse('puzzles.views.answer_queue'))

def handle_puzzle_answer_result(puzzle, answer, result):
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
def answer_queue(request):
    qas = QueuedAnswer.objects.all()
    for qa in qas:
        try:
            sa = SubmittedAnswer.objects.get(puzzle=qa.puzzle, answer=qa.answer, success=True)
            qa.success = True
            qa.user = sa.user
        except Exception:
            qa.success = False
    return render(request, 'puzzles/answer-queue.html', context={
                'queued_answers': qas,
                'refresh': 5
                })

@login_required
def puzzle_call_in_answer(request, puzzle_id):
    puzzle = Puzzle.objects.get(id=puzzle_id)
    if request.method == 'POST':
        form = AnswerForm(request.POST, request.FILES)
        if form.is_valid():
            handle_puzzle_answer(puzzle, request.user, form.cleaned_data['answer'], form.cleaned_data['backsolved'], form.cleaned_data['phone'], request=False)
            return redirect(reverse('puzzles.views.puzzle_info', args=[puzzle_id]))
    else:
        callback_phone = Config.objects.get().callback_phone
        form = AnswerForm(initial={'phone': callback_phone})
        if callback_phone:
            form.fields['phone'].initial = callback_phone
    return render(request, 'puzzles/puzzle-call-in-answer.html', context=puzzle_context(request, {
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
    return render(request, 'puzzles/logout.html')

def logout_return(request):
    return render(request, 'puzzles/logout_return.html', )

@login_required
def welcome(request):
    return redirect(reverse('puzzles.views.overview'))
