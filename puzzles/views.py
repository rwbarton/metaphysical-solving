import random
import os
import os.path
import urllib
import json
import re
import time
import hmac
import base64
import requests

from datetime import timedelta

from collections import defaultdict, Counter

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.template import RequestContext
from django.utils.http import urlencode
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.db import IntegrityError
from django import forms
from django.db.models import Prefetch
from django.db.transaction import atomic, non_atomic_requests
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.timezone import now

from puzzles.models import AccessLog, Config, JitsiRooms, Location, Priority, Puzzle, PuzzleWrongAnswer, QueuedAnswer, Round, Status, SubmittedAnswer, Tag, TagList, UploadedFile, User, UserProfile, quantizedTime
from puzzles.forms import UploadForm, AnswerForm, HintForm

from puzzles.submit import submit_answer
from puzzles.zulip import zulip_send
from puzzles.jaas_jwt import JaaSJwtBuilder
from django.contrib.auth.models import User
from django.conf import settings

jaas_api_key = open('/etc/puzzle/jaas_api_key').read()
jaas_app_id = open('/etc/puzzle/jaas_app_id').read()
jaas_private_key = open('/etc/puzzle/id_rsa_jaas').read()
jaas_webhook_secret = open('/etc/puzzle/jaas_webhook_secret').read().strip()
#webhooklog = open("/home/puzzle/webhooklog","a")

def update_user_social_data(strategy, *args, **kwargs):
  response = kwargs['response']
  backend = kwargs['backend']
  user = kwargs['user']
  if response['picture']:
    url = response['picture']
    user_profile, created = UserProfile.objects.get_or_create(user=user)
    user_profile.picture = url
    user_profile.save()

def get_motd():
    try:
        return Config.objects.get().motd
    except (Config.DoesNotExist, Config.MultipleObjectsReturned):
        return "Oops, someone broke this message. Please ask an admin to fix it."

def get_jitsi_data():
    try:
        table = JitsiRooms.objects.all()
        byUserDict = defaultdict(set)
        for row in table:
            byUserDict[row.user].add(row.puzzle)

        user_list = sorted(byUserDict.items())
    except:
        user_list = None
    return user_list


def puzzle_context(request, d):
    d1 = dict(d)
    d1['teamname'] = settings.TEAMNAME
    d1['motd'] = get_motd()
    d1['hqphone'] = settings.HQPHONE
    d1['hqemail'] = settings.HQEMAIL
    d1['locations'] = Location.objects.all()
    d1['my_puzzles'] = request.user.puzzle_set.order_by('id')
    d1['path'] = request.path
    d1['jitsi_base_url']=settings.JITSI_SERVER_URL
    d1['zulip_url']=settings.ZULIP_SERVER_URL
    d1['admin_link']=settings.SHOW_ADMIN_LINK
    if 'body' in request.GET:
        d1['body_only'] = True
    return d1

def deprecated_log_a_view(puzzle,user):
    previous = AccessLog.objects.filter(puzzle__exact=puzzle,user__exact=user)
    if (previous):
        a = previous.get()
        if (now()-a.lastUpdate)>timedelta(seconds=55):
            a.accumulatedMinutes = a.accumulatedMinutes+1
            a.lastUpdate = now()
            a.save()
    else:
        AccessLog.objects.create(puzzle=puzzle,user=user,lastUpdate=now())

@login_required
def api_motd(request):
    try:
        return JsonResponse({"motd": Config.objects.get().motd})
    except (Config.DoesNotExist, Config.MultipleObjectsReturned):
        return JsonResponse({"motd": ""})

@login_required
def api_overview(request):
    
    overview_dict = {}
    overview_dict["default_priority"] = str(Config.objects.get().default_priority)
    
    rounds = Round.objects.prefetch_related(
     Prefetch('puzzle_set', queryset=Puzzle.objects.all(), to_attr='puzzles')
    )

    def quick_puzzle_info(puzzle):
        p_info = {
            "title": puzzle.title,
            "url": puzzle.url,
            "id": puzzle.id,
            "solver_count": puzzle.recent_count(),
            "unopened": puzzle.unopened_theirs(request.user),
            "tags": puzzle.tag_list(),
            "description": puzzle.description,
        }
        if puzzle.answer:
            p_info["answer"] = puzzle.answer
        else:
            p_info["status"] = str(puzzle.status)
        return (p_info)

    rounds_output = []
    for round in rounds:
        round_dict = {}
        round_dict["round"] = round.name
        round_dict["description"] = round.description if round.description else ""
        if round.parent_round:
            round_dict["parent_round"] = round.parent_round.name
        if round.puzzles:
            round_dict["puzzles"] = []
            for puzzle in round.puzzles:
                round_dict["puzzles"].append(quick_puzzle_info(puzzle))
        rounds_output.append(round_dict)
    
    puzzles_without_round = Puzzle.objects.filter(round__isnull=True)
    if puzzles_without_round:
        rounds_output.append(
            {
                "round": "Unassigned",
                "puzzles": [quick_puzzle_info(puzzle) for puzzle in puzzles_without_round]
            }
        )
    
    overview_dict["rounds"] = rounds_output

    return JsonResponse(overview_dict)

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
                    'puzzles': ({'puzzle':puzz,
                                 'solvers':puzz.recent_count(),
                                 'unopened':puzz.unopened_theirs(request.user)}
                                for puzz in Tag.objects.get(id=tag.id).puzzle_set.select_related().all())
                    }
                     for tag in tags),
            'assigned_puzzles': assigned_puzzles,
            # 'jitsi_data': get_jitsi_data(),
            'unassigned_only': unassigned_only,
            'default_priority': Config.objects.get().default_priority,
            'refresh': 120
            })
    return render(request, "puzzles/overview.html", context=context)

@login_required
def overview(request):
    return overview_by(request, Config.objects.get().default_taglist.id)

@login_required
def puzzle_bottom(request, puzzle_id):
    return render(request, "puzzles/puzzle-bottomframes.html", context={
                'id': puzzle_id,
                'title': Puzzle.objects.get(id=puzzle_id).title
                })

@login_required
def puzzle(request, puzzle_id):
    puzzle = Puzzle.objects.select_related().get(id=puzzle_id)
    statuses = Status.objects.all()
    priorities = Priority.objects.all()
    if (settings.ENABLE_ACCESS_LOG):
        puzzle.log_a_view(user=request.user)
    solvers = puzzle.recent_solvers().order_by('first_name', 'last_name')    
    you_solving = request.user in solvers
    other_solvers = [solver for solver in solvers if solver != request.user]
    other_users = [other_user
                   for other_user in User.objects.order_by('first_name', 'last_name')
                   if other_user not in solvers
                   and other_user != request.user]
    queued_answers = puzzle.queuedanswer_set.order_by('-id')
    wrong_answers = puzzle.puzzlewronganswer_set.order_by('-id')
    uploaded_files = puzzle.uploadedfile_set.order_by('id')
    return render(request, "puzzles/puzzle-frames.html", context=puzzle_context(request, {
                'id': puzzle_id,
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
def puzzle_info(request, puzzle_id):
    puzzle = Puzzle.objects.select_related().get(id=puzzle_id)
    statuses = Status.objects.all()
    priorities = Priority.objects.all()
    if (settings.ENABLE_ACCESS_LOG):
        puzzle.log_a_view(user=request.user)
    solvers = puzzle.recent_solvers().order_by('first_name', 'last_name')
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
def puzzle_linkout(request,puzzle_id):
    puzzle = Puzzle.objects.get(id=puzzle_id) 
    userLog = AccessLog.objects.get_or_create(puzzle=puzzle,user=request.user)[0]
    userLog.linkedOut = True
    userLog.save()
    return redirect(puzzle.url)

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
    if (settings.ENABLE_ACCESS_LOG):
        a = AccessLog(user=solver,puzzle=puzzle)
        a.save()
    else:
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
def handle_puzzle_hint(request, puzzle, user, details, urgent):
    print (puzzle,user,details,urgent)

@login_required
def puzzle_request_hint(request, puzzle_id):
    puzzle = Puzzle.objects.get(id=puzzle_id)
    if request.method == 'POST':
        form = HintForm(request.POST, request.FILES)
        if form.is_valid():
            handle_puzzle_hint(request,puzzle=puzzle, user=request.user, details=form.cleaned_data['details'], urgent = form.cleaned_data['urgent'])
            return redirect(reverse('puzzles.views.puzzle_info', args=[puzzle_id]))
    else:
        form = HintForm(initial={'urgent': False})
    return render(request, 'puzzles/puzzle-request-hint.html', context=puzzle_context(request, {
                'form': form,
                'puzzle': puzzle
                }))

@login_required
def user_location(request):
    if request.method == "POST":
        location = Location.objects.get(name=request.POST['location'])
        request.user.userprofile.location = location
        request.user.userprofile.save()

        # Re-retrieve the location from the database
        updated_location = request.user.userprofile.location
        return JsonResponse({"location": updated_location.name})

    return JsonResponse({"error": "Invalid request method"}, status=400)

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

@login_required
def puzzle_view_history(request, puzzle_id):
    puzzle = Puzzle.objects.select_related().get(id=puzzle_id)
    dedupedLogs = puzzle.all_distinct_logs()
    countTuples = dedupedLogs.values_list("user","accumulatedMinutes")
    displayTuples = [(User.objects.get(id=c[0]),c[1]/60.) for c in countTuples]
    return render(request, "puzzles/view_history.html", context=puzzle_context(request, {
        'puzzle': puzzle,
        'current_solvers': puzzle.recent_solvers(),
        'historical_solvers': displayTuples
                }))

@login_required
def jitsi_page(request,room_id, start_muted=False):
    token = JaaSJwtBuilder().withDefaults() \
        .withApiKey(jaas_api_key) \
            .withUserName(request.user.first_name+" "+request.user.last_name) \
                .withUserEmail(request.user.email) \
                    .withModerator(False) \
                        .withAppID(jaas_app_id) \
                            .withUserAvatar("https://asda.com/avatar") \
                                .signWith(jaas_private_key)
    
    return render(request, "puzzles/jitsi_page.html",
                  context=puzzle_context(request, {
                      'puzzle':puzzle,
                      'jaas_app_id':jaas_app_id,
                      'jitsi_room_id':jaas_app_id+"/"+room_id,
                      'jwt':token.decode(encoding='utf-8'),
                      'start_muted': start_muted,
                  } ))
    
@login_required
def puzzle_jitsi_page(request, puzzle_id):
    start_muted = bool(request.GET.get('start_muted'))
    puzzle = Puzzle.objects.select_related().get(id=puzzle_id)
    return jitsi_page(request,puzzle.jitsi_room_id(), start_muted)

@login_required
def who_what(request):
    all_recent = AccessLog.objects.filter(lastUpdate__gte=now()-timedelta(seconds=120)).distinct()
    jitsi_rooms = JitsiRooms.objects.all()
    rdict = defaultdict(lambda: {"puzzles": set(), "rooms": set()})
    for el in all_recent:
        rdict[el.user]["puzzles"].add(el.puzzle)
    for room in jitsi_rooms:
        if room.puzzle:
            rdict[room.user]["rooms"].add(room.puzzle)
    people = list(rdict.items())
#    print(people)
    return render(request, "puzzles/whowhat.html", context = puzzle_context(request,{
        'people':people}))
    
@login_required
def profile_photo(request):
    user_profile = request.user.userprofile
    if user_profile.picture:
        response = requests.get(user_profile.picture, stream=True)
        if response.status_code == 200:
            return HttpResponse(
                response.content,
                content_type=response.headers['Content-Type']
            )
    return HttpResponse(status=response.status_code)

@csrf_exempt
@require_POST
@non_atomic_requests
def jaas_webhook(request):
    jaas_signature = request.headers["X-Jaas-Signature"]
    sigdict = {k:v for k,v in (element.split('=',maxsplit=1)
                for element in jaas_signature.split(','))}
    payload_to_sign = sigdict["t"]+"."+request.body.decode("utf-8")
    signed = base64.b64encode(hmac.digest(
        jaas_webhook_secret.encode(),
        payload_to_sign.encode(),digest='sha256'))
    if hmac.compare_digest(signed,sigdict["v1"].encode()):
        bdict = json.loads(request.body)
        email = bdict["data"]["email"]
        solver = User.objects.get(email=email)
        room_id = bdict["fqn"].split("/")[1]
        match_obj = re.match(r"^(\w+)-(\d+)-(\w+)$",room_id)
        if match_obj:
            puzzle_id = int(match_obj[2])
            puzzle = Puzzle.objects.get(id=puzzle_id)
            other_id = ''
        else:
            puzzle = None
            other_id = room_id

        event_type = bdict["eventType"]
        if event_type=="PARTICIPANT_JOINED":
            #            webhooklog.write("%s joined %d!\n"%(email,puzzle_id))
            JitsiRooms(user=solver,puzzle=puzzle,string_id=other_id).save()
        elif event_type=="PARTICIPANT_LEFT":
            #            webhooklog.write("%s left %d!\n"%(email,puzzle_id))
            jr = JitsiRooms.objects.filter(user=solver,puzzle=puzzle, string_id=other_id).first()
            jr.delete()
            #        else:
            #            webhooklog.write("unhandled event type %s\n"%bdict["event_type"])
            #    else:
            #        webhooklog.write("verification failed\n")
            #    webhooklog.flush()
        
    return HttpResponse("Message received okay.", content_type="text/plain")
