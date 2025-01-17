from django.db import models, IntegrityError
from ordered_model.models import OrderedModel

from django.contrib.auth.models import User
from django.db.models.signals import pre_save, post_save, m2m_changed
from django.urls import reverse
from django.conf import settings
from django.utils.timezone import now
from django.utils.text import slugify
from collections import defaultdict
from math import ceil
from ago import human

import re
import hashlib
import time
from datetime import timedelta




try:
    # Secret used to generate Jitsi room names.
    jitsi_secret = open('/etc/puzzle/jitsi-secret').read()
    if jitsi_secret == '':
        jitsi_secret = None
except IOError:
    jitsi_secret = None

def quantizedTime():
    return int(time.time()/120)

class Config(models.Model):
    default_status = models.ForeignKey('Status', on_delete=models.CASCADE)
    default_priority = models.ForeignKey('Priority', on_delete=models.CASCADE)
    default_tag = models.ForeignKey('Tag', on_delete=models.SET_NULL,blank=True, null=True)
    default_taglist = models.ForeignKey('TagList', on_delete=models.CASCADE,
                                        help_text="This isn't actually used for anything (at the moment)")

    default_template = models.ForeignKey('PuzzleTemplate',null=True,blank=True,on_delete=models.SET_NULL,
                                         help_text="Default spreadsheet to use to create new puzzles.  Leave null to create completely blank ones")
    default_folder = models.ForeignKey('PuzzleFolder',null=True,blank=True,on_delete=models.SET_NULL,
                                       help_text="Default Folder to use to share new puzzles.  Leave null to share by making world-editable instead")
    callback_phone = models.CharField(max_length=255, blank=True,
                                      help_text="""Phone number on which answer callbacks from Hunt HQ will be received.
If empty, users will have to enter their own phone number when submitting an answer.""")
    use_adc = models.BooleanField(default=False,help_text="Should puzzle Sheets be owned by a real user instead of a service account")

    motd = models.TextField(blank=True)

from puzzles.googlespreadsheet import create_google_spreadsheet, create_google_folder, grant_access
from puzzles.zulip import zulip_send, zulip_create_user

class Status(OrderedModel):
    text = models.CharField(max_length=200)
    css_name = models.SlugField(max_length=200, unique=True)

    class Meta(OrderedModel.Meta):
        verbose_name_plural = 'statuses'

    def __str__(self):
        return self.text

class Priority(OrderedModel):
    text = models.CharField(max_length=200)
    css_name = models.SlugField(max_length=200, unique=True)

    class Meta(OrderedModel.Meta):
        verbose_name_plural = 'priorities'

    def __str__(self):
        return self.text
    

# A single puzzle round, has a name, a description, and a reference to the parent round (parent_round),
# which can be empty. If a round is a parent to multiple rounds, then `child_rounds` field will retrieve
# them all.
class Round(OrderedModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    parent_round = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        related_name='child_rounds',
        blank=True,
        null=True
    )
    def __str__(self):
        return self.name

class Tag(OrderedModel):
    name = models.CharField(max_length=200, unique=True)

    def topic(self):
        return '%s-%d'%(slugify(self.name),self.id)

    def __str__(self):
        return self.name

class AutoTag(models.Model):
    html_name = models.CharField(max_length=200)
    tag = models.ForeignKey('Tag', on_delete=models.CASCADE)

    def __str__(self):
        return self.html_name

class QueuedAnswer(models.Model):
    # An answer that's not wrong yet!
    puzzle = models.ForeignKey('Puzzle', on_delete=models.CASCADE)
    answer = models.CharField(max_length=200)

    class Meta:
        unique_together = ('puzzle', 'answer')

    def __str__(self):
        return 'answer "%s" for puzzle "%s"' % (self.answer, self.puzzle.title)

class QueuedHint(OrderedModel):
    puzzle = models.ForeignKey('Puzzle', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    urgent = models.BooleanField(default=False)
    details = models.TextField(blank=True, null=True)
    response = models.TextField(blank=True, null=True)
    resolved = models.BooleanField(default=False)
    createdTime = models.DateTimeField(auto_now_add=True)
    modifiedTime = models.DateTimeField(auto_now=True)

    def submitted_ago(self):
        return (human(timedelta(seconds=ceil((now() - self.createdTime).total_seconds() / 60) * 60)))

    def __str__(self):
        return '%s on "%s"' % (self.user, self.puzzle.title)


class SubmittedAnswer(models.Model):
    puzzle = models.ForeignKey('Puzzle', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    answer = models.CharField(max_length=200)
    backsolved = models.BooleanField()
    phone = models.CharField(max_length=30)

    timestamp = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=False)
    response = models.TextField(default='')

    def __str__(self):
        return '%s: %s' % (self.puzzle.title, self.answer)

class PuzzleWrongAnswer(models.Model):
    puzzle = models.ForeignKey('Puzzle', on_delete=models.CASCADE)
    answer = models.CharField(max_length=200)

    class Meta:
        unique_together = ('puzzle', 'answer')

    def __str__(self):
        return 'answer "%s" for puzzle "%s"' % (self.answer, self.puzzle.title)

def wrong_answer_message(**kwargs):
    if kwargs['created']:
        wa = kwargs['instance']
        zulip_send(user='b+status',
                   stream='p%d' % (wa.puzzle.id,),
                   subject='wrong answer',
                   message='Wrong answer: %s' % wa.answer)

post_save.connect(wrong_answer_message, sender=PuzzleWrongAnswer)

def defaultStatus():
    return Config.objects.get().default_status
def defaultPriority():
    return Config.objects.get().default_priority
def defaultTags():
    return [Config.objects.get().default_tag]
def defaultTemplate():
    return Config.objects.get().default_template
def defaultFolder():
    return Config.objects.get().default_folder


class Puzzle(OrderedModel):
    title = models.CharField(max_length=200)
    url = models.URLField(unique=True)

    status = models.ForeignKey('Status', default=defaultStatus, on_delete=models.SET_DEFAULT)
    priority = models.ForeignKey('Priority', default=defaultPriority, on_delete=models.SET_DEFAULT)
    tags = models.ManyToManyField('Tag', default=defaultTags, blank=True)

    description = models.CharField(max_length=280, blank=True, help_text="Short description of the given puzzle")

    round = models.ForeignKey('Round', null=True, blank=True, on_delete=models.SET_NULL, help_text="The round a given puzzle belongs to.")

    solvers = models.ManyToManyField(User, blank=True)
    topic_name = models.CharField(max_length=200,blank=True)
    spreadsheet = models.URLField(blank=True)
    answer = models.CharField(max_length=200, blank=True)
    checkAnswerLink = models.URLField(blank=True)
    template = models.ForeignKey('PuzzleTemplate',null=True,blank=True,default=defaultTemplate, on_delete=models.SET_NULL,
                                 help_text="Template to copy when first making this puzzle.  Leave null to create from scratch.")
    folder = models.ForeignKey('PuzzleFolder',null=True,blank=True,default=defaultFolder, on_delete=models.SET_NULL,
                               help_text="Google Drive folder to use to share this puzzle spreadsheet when first making it.  Leave null to share by making world-editable instead.")

    def __str__(self):
        return self.title
    
    def tag_list(self):
        return [tag.name for tag in self.tags.all()]

    def answer_or_status(self):
        if self.answer:
            return {'answer': self.answer}
        else:
            return {'status': self.status}

    def zulip_topic(self):
        if not self.topic_name:
            self.topic_name = '%s-%d'%(slugify(self.title),self.id)
            self.save()
        return self.topic_name

    def jitsi_room_id(self):
        if jitsi_secret is None:
            return None
        id_hash = hashlib.sha1(('%d-%s' % (self.id, jitsi_secret)).encode()).hexdigest()[0:16]
        return '%s-%d-%s' % (re.sub(r'[^a-zA-Z0-9]','',self.title),self.id, id_hash)

    def jitsi_room_url(self):
        return reverse("puzzles.views.puzzle_jitsi_page",args=[self.id])
        
    def log_a_view(self,user):
        userLog = AccessLog.objects.get_or_create(puzzle=self,user=user)[0]
        if (now()-userLog.lastUpdate)>timedelta(seconds=355):
            userLog.accumulatedMinutes = userLog.accumulatedMinutes+6
            userLog.lastUpdate = now()
            userLog.save()

    def all_distinct_logs(self):
        return AccessLog.objects.filter(puzzle__exact=self).distinct()
    def recent_logs(self):
        return self.all_distinct_logs().filter(lastUpdate__gte = now()-timedelta(seconds=360))
    def recent_count(self):
        return self.recent_logs().order_by("user").values("user").distinct().count()
    
    def unopened_theirs(self,user):
        a = self.all_distinct_logs().filter(user__exact=user)
        return not (a and a.get().linkedOut)
        
    #if called without a user, has *anyone* opened this page on our server
    def unopened_ours(self,user=None):
        if user:
            a = self.all_distinct_logs().filter(user__exact=user)
            return not (a and a.get().accumulatedMinutes>0)
        else:
            return self.all_distinct_logs().filter(accumulatedMinutes__gte=1).count()<=0
    
    def effort_spent(self):
        dedupedLogs = self.all_distinct_logs()
        countTuples = dedupedLogs.values_list("user","accumulatedMinutes")
        individualValues = [round(c[1]/60., 2) for c in countTuples]
        return({
            "solvers": len(individualValues),
            "solver_hours": sum(individualValues)
        })

    def recent_solvers(self):
        logs=self.recent_logs()
        return User.objects.filter(id__in=[urec["user"] for urec in logs.order_by("user").values("user").distinct()])

    def save(self, *args, **kwargs):
        # Grab old instance to see if our answer is new.
        try:
            old_puzzle = Puzzle.objects.get(id=self.id)
            old_answer = old_puzzle.answer
        except Puzzle.DoesNotExist:
            old_answer = ''

        # Save first, so that we don't create a new spreadsheet if the
        # save would fail.
        super(Puzzle, self).save(*args, **kwargs)

        if self.spreadsheet == '':
            self.spreadsheet = create_google_spreadsheet(title = self.title,
                                                         folder= self.folder,
                                                         puzzle_template=self.template,
                                                         )['spreadsheetUrl']
            # create() uses force_insert, override that here.
            kwargs['force_update'] = True
            kwargs['force_insert'] = False
            super(Puzzle, self).save(*args, **kwargs)

        if self.answer != old_answer:
            zulip_send(user='b+status',
                       stream='puzzles',
                       subject=self.zulip_topic(),
                       message=':thumbs_up: **%s** is correct!' % self.answer)

            zulip_send(user='b+status',
                       stream='status',
                       subject='solved',
                       message='Puzzle %s solved [%s]' % (self.title, self.round))

def send_puzzle_zulip(**kwargs):
    if kwargs['created']:
        puzzle = kwargs['instance']
        zulip_send(user='b+status',
                   stream='puzzles',
                   subject=puzzle.zulip_topic(),
                   message='New puzzle "%s"' % (puzzle.title,))
        zulip_send(user='b+status',
                   stream='status',
                   subject='new puzzle',
                   message='New puzzle [%s](%s) ([p%d](%s))' %
                   (puzzle.title, puzzle.url, puzzle.id,
                    settings.BASE_URL + reverse('puzzles.views.puzzle', args=[puzzle.id])))

def notify_of_new_tag(**kwargs):
    if kwargs['created']:
        tag = kwargs['instance']
        zulip_send(user='b+status',
                   stream="tags",
                   subject=tag.topic(),
                   message='New tag %s (%s)' % (tag.name, tag.topic()))
        zulip_send(user='b+status',
                   stream='status',
                   subject='new tag',
                   message='New tag created: "%s", follow at [#tags>%s](%s)'%(tag.name,tag.topic(),
                                                                              "%s/#narrow/stream/tags/topic/%s" % (settings.ZULIP_SERVER_URL,tag.topic())))

def notify_tag_on_add(**kwargs):
    if kwargs['action'] == 'pre_add':
        puzzle = kwargs['instance']
        pks = kwargs['pk_set']
        prev_tag_pks = [tag.id for tag in puzzle.tags.all()]
        for pk in pks:
            if pk not in prev_tag_pks:
                tag = Tag.objects.get(id=pk)
                print("Tag %d added to puzzle %s"%(pk, puzzle.title))
                zulip_send(user='b+status',
                           stream="tags",
                           subject=tag.topic(),
                           message='Puzzle [%s](%s) ([p%d](%s)) tagged as %s' %
                                   (puzzle.title, puzzle.url, puzzle.id,
                                    settings.BASE_URL + reverse('puzzles.views.puzzle', args=[puzzle.id]),
                                    tag))

post_save.connect(send_puzzle_zulip, sender=Puzzle)
post_save.connect(notify_of_new_tag, sender=Tag)
m2m_changed.connect(notify_tag_on_add, sender = Puzzle.tags.through)

class TagList(OrderedModel):
    name = models.CharField(max_length=200, unique=True)
    tags = models.ManyToManyField('Tag')

    def __str__(self):
        return self.name

class UploadedFile(models.Model):
    puzzle = models.ForeignKey('Puzzle', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    url = models.URLField()

class Location(OrderedModel):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    location = models.ForeignKey('Location', on_delete=models.CASCADE)
    picture = models.TextField(null=True, blank=True)

class UserZulipStatus(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    NONE = 'none'
    SUCCESS = 'success'
    FAILURE = 'failure'
    STATUS_CHOICES = (
        (NONE, 'Not created yet'),
        (SUCCESS, 'Zulip user successfully created'),
        (FAILURE, 'Zulip user could not be created'),
        )
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=NONE)

def make_user_profile(**kwargs):
    user = kwargs['instance']
    default_location = Location.objects.get(name='unknown')
    user_profile, _ = UserProfile.objects.get_or_create(
        user=user,
        defaults={'location': default_location})
    grant_access((folder.fid for folder in PuzzleFolder.objects.filter(shareOnly__isnull=True)),[user.email])
    user_zulip_status, _ = UserZulipStatus.objects.get_or_create(user=user)
    if user_zulip_status.status == UserZulipStatus.NONE \
            and user.first_name:
        success = zulip_create_user(user.email, '%s %s' % (user.first_name, user.last_name), user.first_name)
        if success:
            user_zulip_status.status = UserZulipStatus.SUCCESS
        else:
            user_zulip_status.status = UserZulipStatus.FAILURE
        user_zulip_status.save()

post_save.connect(make_user_profile, sender=User)

def make_superuser(**kwargs):
    user = kwargs['instance']
    user.is_staff = True
    user.is_superuser = True

pre_save.connect(make_superuser, sender=User)

class AccessLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    puzzle = models.ForeignKey('Puzzle', on_delete=models.CASCADE)
    linkedOut = models.BooleanField(default=False)
    accumulatedMinutes = models.IntegerField(default=0)
    lastUpdate = models.DateTimeField(default=now)
    def __str__(self):
        return self.puzzle.title + " / " + self.user.email

class JitsiRooms(OrderedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    puzzle = models.ForeignKey('Puzzle', on_delete=models.CASCADE, null=True)
    string_id = models.CharField(max_length=200,default='')

class PuzzleFolder(OrderedModel):
    name = models.CharField(max_length=200,unique=True)
    fid = models.CharField(max_length=200,blank=True)
    shareOnly = models.ForeignKey(User,null=True, blank=True, on_delete=models.SET_NULL,
                                  help_text="User to share this folder with.  Leave null (default) to share with all users")
    def save(self, *args, **kwargs):

        super(PuzzleFolder, self).save(*args, **kwargs)

        if (self.fid == ''):
            self.fid = create_google_folder(self.name)
            kwargs['force_update'] = True
            kwargs['force_insert'] = False
            super(PuzzleFolder, self).save(*args, **kwargs)

        if (self.shareOnly):
            grant_access([self.fid],[self.shareOnly.email])
        else:
            grant_access([self.fid],(user.email for user in User.objects.all()))

    def __str__(self):
        return self.name



class PuzzleTemplate(OrderedModel):
    name = models.CharField(max_length=200,unique=True)
    folder = models.ForeignKey('PuzzleFolder',on_delete = models.SET_NULL,null=True)
    fid = models.CharField(max_length=200,blank=True)
    def save(self, *args, **kwargs):

        super(PuzzleTemplate, self).save(*args, **kwargs)

        if self.fid == '':
            self.fid = create_google_spreadsheet(self.name,folder=self.folder,puzzle_template=None)['spreadsheetId']
            kwargs['force_update'] = True
            kwargs['force_insert'] = False
            super(PuzzleTemplate, self).save(*args, **kwargs)
            
    def __str__(self):
        return self.name
        
