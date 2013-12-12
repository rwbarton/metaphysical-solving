from django.db import models, IntegrityError
from ordered_model.models import OrderedModel

from django.contrib.auth.models import User
from django.db.models.signals import pre_save, post_save
import re

from puzzles.googlespreadsheet import create_google_spreadsheet
from puzzles.humbug import humbug_register_email, humbug_registration_finished, humbug_send

class Config(models.Model):
    default_status = models.ForeignKey('Status')
    default_priority = models.ForeignKey('Priority')
    default_tag = models.ForeignKey('Tag')
    default_taglist = models.ForeignKey('TagList')

    motd = models.TextField(blank=True)

class Status(OrderedModel):
    text = models.CharField(max_length=200)
    css_name = models.SlugField(max_length=200, unique=True)

    class Meta(OrderedModel.Meta):
        verbose_name_plural = 'statuses'

    def __unicode__(self):
        return self.text

class Priority(OrderedModel):
    text = models.CharField(max_length=200)
    css_name = models.SlugField(max_length=200, unique=True)

    class Meta(OrderedModel.Meta):
        verbose_name_plural = 'priorities'

    def __unicode__(self):
        return self.text

class Tag(OrderedModel):
    name = models.CharField(max_length=200, unique=True)

    def __unicode__(self):
        return self.name

class QueuedAnswer(models.Model):
    # An answer that's not wrong yet!
    puzzle = models.ForeignKey('Puzzle')
    answer = models.CharField(max_length=200)

    class Meta:
        unique_together = ('puzzle', 'answer')

    def __unicode__(self):
        return 'answer "%s" for puzzle "%s"' % (self.answer, self.puzzle.title)

class PuzzleWrongAnswer(models.Model):
    puzzle = models.ForeignKey('Puzzle')
    answer = models.CharField(max_length=200)

    class Meta:
        unique_together = ('puzzle', 'answer')

    def __unicode__(self):
        return 'answer "%s" for puzzle "%s"' % (self.answer, self.puzzle.title)

def wrong_answer_message(**kwargs):
    if kwargs['created']:
        wa = kwargs['instance']
        humbug_send(user='b+status',
                    stream='p%d' % (wa.puzzle.id,),
                    subject='wrong answer',
                    message='Wrong answer: %s' % wa.answer)

post_save.connect(wrong_answer_message, sender=PuzzleWrongAnswer)

class Puzzle(OrderedModel):
    title = models.CharField(max_length=200)
    url = models.URLField(unique=True)

    status = models.ForeignKey('Status', default=lambda: Config.objects.get().default_status)
    priority = models.ForeignKey('Priority', default=lambda: Config.objects.get().default_priority)
    tags = models.ManyToManyField('Tag', default=lambda: [Config.objects.get().default_tag])

    solvers = models.ManyToManyField(User, blank=True)

    spreadsheet = models.URLField(blank=True)
    answer = models.CharField(max_length=200, blank=True)
    checkAnswerLink = models.URLField(blank=True)

    def __unicode__(self):
        return self.title

    def answer_or_status(self):
        if self.answer:
            return {'answer': self.answer}
        else:
            return {'status': self.status}

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
            humbug_send(user='b+status',
                        stream='p%d' % (self.id,),
                        subject='solved!',
                        message=':thumbsup: **%s**' % self.answer)

            humbug_send(user='b+status',
                        stream='status',
                        subject='solved',
                        message='Puzzle %s solved' % (self.title,))

def send_puzzle_humbug(**kwargs):
    if kwargs['created']:
        puzzle = kwargs['instance']
        humbug_send(user='b+status',
                    stream='p%d' % (puzzle.id,),
                    subject='new',
                    message='New puzzle "%s"' % (puzzle.title,))
        humbug_send(user='b+status',
                    stream='status',
                    subject='new puzzle',
                    message='New puzzle [%s](%s)' % (puzzle.title, puzzle.url))

post_save.connect(send_puzzle_humbug, sender=Puzzle)

class TagList(OrderedModel):
    name = models.CharField(max_length=200, unique=True)
    tags = models.ManyToManyField('Tag')

    def __unicode__(self):
        return self.name

class UploadedFile(models.Model):
    puzzle = models.ForeignKey('Puzzle')
    name = models.CharField(max_length=200)
    url = models.URLField()

class Location(OrderedModel):
    name = models.CharField(max_length=200, unique=True)

    def __unicode__(self):
        return self.name

def user_to_email(user):
    return 's+%d@metaphysicalplant.com' % (user.id,)

class UserProfile(models.Model):
    user = models.OneToOneField(User)

    location = models.ForeignKey('Location')
    has_humbug_account = models.BooleanField()
    # Humbug account email addresses are based off the *user* id (not user_profile)

    def finished_humbug_registration(self):
        if self.has_humbug_account:
            return True
        if humbug_registration_finished(user_to_email(self.user)):
            self.has_humbug_account = True
            self.save()
            return True
        return False

class HumbugConfirmation(models.Model):
    email = models.CharField(max_length=63, unique=True)
    confirmation_url = models.URLField()

def humbug_register(**kwargs):
    if kwargs['created']:
        user = kwargs['instance']
        humbug_register_email(user_to_email(user))

# post_save.connect(humbug_register, sender=User)

def make_user_profile(**kwargs):
    user = kwargs['instance']
    default_location = Location.objects.get(name='unknown')
    try:
        UserProfile(user=user, location=default_location, has_humbug_account=False).save()
    except IntegrityError:
        # user profile already exists, do nothing
        pass

post_save.connect(make_user_profile, sender=User)

def make_superuser(**kwargs):
    user = kwargs['instance']
    user.is_staff = True
    user.is_superuser = True

pre_save.connect(make_superuser, sender=User)
