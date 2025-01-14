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
from django.db import IntegrityError, transaction
from django import forms
from django.db.models import Prefetch
from django.db.transaction import atomic, non_atomic_requests
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.timezone import now

from puzzles.models import AccessLog, Config, JitsiRooms, Location, Priority, Puzzle, PuzzleWrongAnswer, QueuedAnswer, \
    Round, Status, SubmittedAnswer, Tag, TagList, UploadedFile, User, UserProfile, quantizedTime, QueuedHint
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

# This function is called as part of the auth flow (defined in settings.py), and updates the URL
# for the user's Google profile photo
def update_user_social_data(strategy, *args, **kwargs):
  response = kwargs['response']
  backend = kwargs['backend']
  user = kwargs['user']
  if response['picture']:
    url = response['picture']
    user_profile, created = UserProfile.objects.get_or_create(user=user)
    user_profile.picture = url
    user_profile.save()

# This is a helper function that retrieves the message of the day
def get_motd():
    try:
        return Config.objects.get().motd
    except (Config.DoesNotExist, Config.MultipleObjectsReturned):
        return "Oops, someone broke this message. Please ask an admin to fix it."

# This is a helper function that retrieves Jitsi data
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

# This provides base context for template views
def base_context(d = {}):
    d1 = dict(d)
    d1['teamname'] = settings.TEAMNAME
    d1['hqphone'] = settings.HQPHONE
    d1['hqemail'] = settings.HQEMAIL
    d1['locations'] = Location.objects.all()
    d1['admin_link']=settings.SHOW_ADMIN_LINK
    return(d1)

# An API endpoint for updating user location
@login_required
def api_user_location(request):
    if request.method == "POST":
        location = Location.objects.get(name=request.POST['location'])
        request.user.userprofile.location = location
        request.user.userprofile.save()

        # Re-retrieve the location from the database
        updated_location = request.user.userprofile.location
        return JsonResponse({"location": updated_location.name})

    return JsonResponse({"error": "Invalid request method"}, status=400)

# API endpoint for uploading multiple files for a puzzle
@login_required
def api_upload_files(request, puzzle_id):
    if request.method != "POST":
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        puzzle = Puzzle.objects.get(id=puzzle_id)
        files = request.FILES.getlist('files')
        names = request.POST.getlist('names')
    
        if not files:
            return JsonResponse({"error": "No files provided"}, status=400)

        for file, name in zip(files, names):

            upload = UploadedFile.objects.create(
                puzzle=puzzle,
                name=name
            )

            upload_dir = os.path.join('/var/www/uploads', str(puzzle.id), str(upload.id))
            os.makedirs(upload_dir, exist_ok=True)

            file_path = os.path.join(upload_dir, file.name)
            with open(file_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            
            upload.url = f"{settings.BASE_URL}/uploads/{puzzle.id}/{upload.id}/{file.name}"
            upload.save()
        
        puzzle_files = [{"filename": file.name, "url": str(file.url)} for file in puzzle.uploadedfile_set.order_by('id')]

        return JsonResponse({
            "files": puzzle_files
        })

    except Puzzle.DoesNotExist:
        return JsonResponse({'error': 'Puzzle not found'}, status=404)
    except Exception as e:
        print(e)
        return JsonResponse({'error': str(e)}, status=500)            

# API endpoint for getting updates to the page-top message
@login_required
def api_motd(request):
    try:
        return JsonResponse({"motd": Config.objects.get().motd})
    except (Config.DoesNotExist, Config.MultipleObjectsReturned):
        return JsonResponse({"motd": ""})

# API endpoint for getting puzzle's solver history
@login_required
def api_puzzle_history(request, puzzle_id):
    puzzle = Puzzle.objects.prefetch_related('accesslog_set').get(id=puzzle_id)
    dedupedLogs = puzzle.all_distinct_logs()
    countTuples = dedupedLogs.values_list("user","accumulatedMinutes")
    displayTuples = [(User.objects.get(id=c[0]),c[1]/60.) for c in countTuples]
    prior_viewers = [{
        "id": item[0].id, 
        "first_name": item[0].first_name,
        "last_name": item[0].last_name,
        "location": item[0].userprofile.location.name,
        "hours": round(item[1], 2)
        } for item in displayTuples]
    current_viewers = puzzle.recent_solvers().order_by('first_name', 'last_name')
    current_viewers = [{
        "id": item.id,
        "first_name": item.first_name,
        "last_name": item.last_name,
        "location": item.userprofile.location.name,
    } for item in current_viewers]
    return JsonResponse({
        "current_viewers": current_viewers,
        "prior_viewers": prior_viewers,
    }) 

# API endpoint for getting full overview data
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
            "priority": str(puzzle.priority),
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
    overview_dict["statuses"] = [str(status) for status in Status.objects.all()]
    overview_dict["priorities"] = [str(priority) for priority in Priority.objects.all()]

    return JsonResponse(overview_dict)

# Helper function for building a full puzzle info dict
def build_puzzle_dict(user, puzzle_id):
    puzzle_dict = {}
    puzzle_dict["tags"] = [str(tag) for tag in Tag.objects.all()]
    puzzle_dict["statuses"] = [str(status) for status in Status.objects.all()]
    puzzle_dict["priorities"] = [str(priority) for priority in Priority.objects.all()]
    
    puzzle = Puzzle.objects.select_related().get(id=puzzle_id)

    p_info = {
        "title": puzzle.title,
        "url": puzzle.url,
        "id": puzzle.id,
        "hints": [{"user": hint.user.first_name + " " + hint.user.last_name,
                          "details": hint.details} for hint in puzzle.queuedhint_set.order_by('-id')],
        "tags": puzzle.tag_list(),
        "description": puzzle.description,
        "priority": str(puzzle.priority),
        'jitsi_room_id': puzzle.jitsi_room_id(),
    }

    solvers = [{"name": (solver.first_name + " " + solver.last_name),
                     "id": solver.id} for solver in puzzle.recent_solvers().order_by('first_name', 'last_name')]

    puzzle_files = [{"filename": file.name, "url": str(file.url)} for file in puzzle.uploadedfile_set.order_by('id')]

    queued_answers = [answer.answer for answer in puzzle.queuedanswer_set.order_by('-id')]

    wrong_answers = [answer.answer for answer in puzzle.puzzlewronganswer_set.order_by('-id')]

    if queued_answers or wrong_answers:
        p_info["prior_answers"] = {}
        if queued_answers:
            p_info["prior_answers"]["queued"] = queued_answers
        if wrong_answers:
            p_info["prior_answers"]["wrong"] = wrong_answers

    if solvers:
        p_info["solvers"] = solvers

    if puzzle_files:
        p_info["uploaded_files"] = puzzle_files

    if puzzle.round:
        p_info["round"] = str(puzzle.round)

    if puzzle.answer:
        p_info["answer"] = puzzle.answer
    else:
        p_info["status"] = str(puzzle.status)
    
    puzzle_dict["puzzle"] = p_info

    return(puzzle_dict)

# API endpoint for getting a single puzzle's data in JSON forat
@login_required
def api_puzzle(request, puzzle_id):

    puzzle_dict = build_puzzle_dict(request.user, puzzle_id)

    return JsonResponse(puzzle_dict)

# API endpoint for updating a puzzle's priority, status, description,
# or tags
@login_required
def api_update_puzzle (request, puzzle_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)  # Parse JSON body
            puzzle = Puzzle.objects.get(id=puzzle_id)
            for key in data:
                if key == "priority":                  
                    priority = Priority.objects.get(text=data["priority"])
                    puzzle.priority = priority
                if key == "status":
                    status = Status.objects.get(text=data["status"])
                    puzzle.status = status
                if key == "description":
                    puzzle.description = data["description"]
                if key == "tags":
                    with transaction.atomic():
                        tags = [Tag.objects.get_or_create(name=name)[0] for name in data["tags"]]
                        puzzle.tags.set(tags)
            puzzle.save()
            return JsonResponse(build_puzzle_dict(request.user, puzzle_id))
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

# API endpoint for logging a user's view
@login_required
def api_log_a_view(request, puzzle_id):
    puzzle = Puzzle.objects.get(id=puzzle_id)
    if puzzle:
        puzzle.log_a_view(user=request.user)
        return HttpResponse(status=204)
    else:
        return HttpResponse(status=418)

# Main overview page
@login_required
def overview(request):
    return render(request, "puzzles/overview.html", context=base_context())

# Single puzzle page
@login_required
def puzzle(request, puzzle_id):
    puzzle = Puzzle.objects.get(id=puzzle_id)
    return render(request, "puzzles/puzzle.html", context = base_context({
                'id': puzzle_id,
                'title': puzzle.title,
                'refresh': 60
                }))

# A redirector to puzzle's external page with view logging
@login_required
def puzzle_linkout(request,puzzle_id):
    puzzle = Puzzle.objects.get(id=puzzle_id) 
    userLog = AccessLog.objects.get_or_create(puzzle=puzzle,user=request.user)[0]
    userLog.linkedOut = True
    userLog.save()
    return redirect(puzzle.url)

# Redirector to the puzzle's Google Sheet
@login_required
def puzzle_spreadsheet(request, puzzle_id):
    spreadsheet = Puzzle.objects.get(id=puzzle_id).spreadsheet
    if spreadsheet:
        return redirect(spreadsheet)
    return HttpResponse("Oops, the spreadsheet isn't ready quite yet. Please wait a moment and then <a href=\"\">refresh</a> this pane.")

# Redirector to the puzzle's Zulip chat
@login_required
def puzzle_chat(request, puzzle_id):
    return redirect("%s/#narrow/stream/puzzles/topic/p%d" % (settings.ZULIP_SERVER_URL,int(puzzle_id)))

# Used for the main answer queue page to manage answer queue manually
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

# Used for the main answer queue page to manage answer queue manually
@login_required
def answer_submit_result(request, answer_id, result):
    queued_answer = QueuedAnswer.objects.get(id=answer_id)
    handle_puzzle_answer_result(queued_answer.puzzle, queued_answer.answer, result)
    queued_answer.delete()
    return redirect(reverse('puzzles.views.answer_queue'))

# Used for the main answer queue page to manage answer queue manually
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

# Manual answer queue page
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
def handle_puzzle_hint(request, puzzle, user, details, urgent):
    q=QueuedHint(puzzle=puzzle, user=user, details=details, urgent=urgent, resolved=False)
    q.save()

@login_required
def puzzle_request_hint(request, puzzle_id):
    puzzle = Puzzle.objects.get(id=puzzle_id)
    if request.method == 'POST':
        form = HintForm(request.POST, request.FILES)
        if form.is_valid():
            handle_puzzle_hint(request,puzzle=puzzle, user=request.user,
                               details=form.cleaned_data['details'],
                               urgent = form.cleaned_data['urgent'])
            return redirect(reverse('puzzles.views.puzzle_info', args=[puzzle_id]))
    else:
        form = HintForm(initial={'urgent': False})
    return render(request, 'puzzles/puzzle-request-hint.html', context=puzzle_context(request, {
                'form': form,
                'puzzle': puzzle
                }))

@login_required
def hint_queue(request):
    queued_hints = QueuedHint.objects.all()
    return render(request, 'puzzles/hint-queue.html', context=base_context({
                'queued_hints': queued_hints.filter(resolved=False),
                'resolved_hints': queued_hints.filter(resolved=True),
                'refresh': 5
                }))

@login_required
def hint_resolve(request,id):
    q = QueuedHint.objects.get(id=id)
    q.resolved = not q.resolved
    q.save()
    return redirect(reverse('puzzles.views.hint_queue'))

# Auth endpoints

def logout_user(request):
    logout(request)
    return render(request, 'puzzles/logout.html')

def logout_return(request):
    return render(request, 'puzzles/logout_return.html', )

# Main welcome page
@login_required
def welcome(request):
    return redirect(reverse('puzzles.views.overview'))


@login_required
def puzzle_view_history(request, puzzle_id):
    puzzle = Puzzle.objects.select_related().get(id=puzzle_id)
    dedupedLogs = puzzle.all_distinct_logs()
    countTuples = dedupedLogs.values_list("user","accumulatedMinutes")
    displayTuples = [(User.objects.get(id=c[0]),c[1]/60.) for c in countTuples]
    return render(request, "puzzles/view_history.html", context=base_context({
        'puzzle': puzzle,
        'current_solvers': puzzle.recent_solvers(),
        'historical_solvers': displayTuples
                }))

# General Jitsi page
@login_required
def jitsi_page(request, room_id, start_muted=False):
    token = JaaSJwtBuilder().withDefaults() \
        .withApiKey(jaas_api_key) \
            .withUserName(request.user.first_name+" "+request.user.last_name) \
                .withUserEmail(request.user.email) \
                    .withModerator(False) \
                        .withAppID(jaas_app_id) \
                            .withUserAvatar(request.user.userprofile.picture) \
                                .signWith(jaas_private_key)
    
    return render(request, "puzzles/jitsi_page.html",
                  context = {
                      'jaas_app_id':jaas_app_id,
                      'jitsi_room_id':jaas_app_id+"/"+room_id,
                      'jwt':token.decode(encoding='utf-8'),
                      'start_muted': start_muted,
                  })

# Puzzle-specific Jitsi page
@login_required
def puzzle_jitsi_page(request, puzzle_id):
    start_muted = bool(request.GET.get('start_muted'))
    puzzle = Puzzle.objects.select_related().get(id=puzzle_id)
    return jitsi_page(request,puzzle.jitsi_room_id(), start_muted)

# Who's on What page
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
    return render(request, "puzzles/whowhat.html", context = base_context(request,{
        'people':people}))

# Google profile photo retriever (direct embedding doesn't work because of
# Google's restrictions)
@login_required
def profile_photo(request, id = None):
    if not id:
        user_profile = request.user.userprofile
    else:
        try:
            user_profile = User.objects.get(id=id).userprofile
        except:
            return HttpResponse(status=404)
    if user_profile.picture:
        response = requests.get(user_profile.picture, stream=True)
        if response.status_code == 200:
            return HttpResponse(
                response.content,
                content_type=response.headers['Content-Type']
            )
    return HttpResponse(status=404)

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
