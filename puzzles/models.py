from django.db import models, IntegrityError
from ordered_model.models import OrderedModel

from django.contrib.auth.models import User
from django.db.models.signals import pre_save, post_save
from django.urls import reverse
from django.conf import settings
import re
import hashlib

from puzzles.googlespreadsheet import create_google_spreadsheet
from puzzles.zulip import zulip_send, zulip_create_user

try:
    # Secret used to generate Jitsi room names.
    jitsi_secret = open('/etc/puzzle/jitsi-secret').read()
    if jitsi_secret == '':
        jitsi_secret = None
except IOError:
    jitsi_secret = None

class Config(models.Model):
    default_status = models.ForeignKey('Status', on_delete=models.CASCADE)
    default_priority = models.ForeignKey('Priority', on_delete=models.CASCADE)
    default_tag = models.ForeignKey('Tag', on_delete=models.CASCADE)
    default_taglist = models.ForeignKey('TagList', on_delete=models.CASCADE)

    callback_phone = models.CharField(max_length=255, blank=True,
                                      help_text="""Phone number on which answer callbacks from Hunt HQ will be received.
If empty, users will have to enter their own phone number when submitting an answer.""")

    motd = models.TextField(blank=True)

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

class Tag(OrderedModel):
    name = models.CharField(max_length=200, unique=True)

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

class Puzzle(OrderedModel):
    title = models.CharField(max_length=200)
    url = models.URLField(unique=True)

    status = models.ForeignKey('Status', default=defaultStatus, on_delete=models.CASCADE)
    priority = models.ForeignKey('Priority', default=defaultPriority, on_delete=models.CASCADE)
    tags = models.ManyToManyField('Tag', default=defaultTags)

    solvers = models.ManyToManyField(User, blank=True)

    spreadsheet = models.URLField(blank=True)
    answer = models.CharField(max_length=200, blank=True)
    checkAnswerLink = models.URLField(blank=True)

    def __str__(self):
        return self.title

    def answer_or_status(self):
        if self.answer:
            return {'answer': self.answer}
        else:
            return {'status': self.status}

    def zulip_stream(self):
        return 'p%d' % (self.id,)

    def jitsi_room_id(self):
        if jitsi_secret is None:
            return None
        id_hash = hashlib.sha1(('%d-%s' % (self.id, jitsi_secret)).encode()).hexdigest()[0:16]
        return '%s-%d-%s' % (re.sub(r'[^a-zA-Z0-9]','',self.title),self.id, id_hash)

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
            self.spreadsheet = create_google_spreadsheet(self.title)
            # create() uses force_insert, override that here.
            kwargs['force_update'] = True
            kwargs['force_insert'] = False
            super(Puzzle, self).save(*args, **kwargs)

        if self.answer != old_answer:
            zulip_send(user='b+status',
                       stream=self.zulip_stream(),
                       subject='solved!',
                       message=':thumbs_up: **%s**' % self.answer)

            zulip_send(user='b+status',
                       stream='status',
                       subject='solved',
                       message='Puzzle %s solved [%s]' % (self.title, ', '.join(str(tag) for tag in self.tags.all())))

def send_puzzle_zulip(**kwargs):
    if kwargs['created']:
        puzzle = kwargs['instance']
        zulip_send(user='b+status',
                   stream=puzzle.zulip_stream(),
                   subject='new',
                   message='New puzzle "%s"' % (puzzle.title,))
        zulip_send(user='b+status',
                   stream='status',
                   subject='new puzzle',
                   message='New puzzle [%s](%s) ([p%d](%s))' %
                   (puzzle.title, puzzle.url, puzzle.id,
                    settings.BASE_URL + reverse('puzzles.views.puzzle', args=[puzzle.id])))

post_save.connect(send_puzzle_zulip, sender=Puzzle)

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
