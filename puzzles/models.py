from django.db import models
from ordered_model.models import OrderedModel

from django.contrib.auth.models import User
from django.db.models.signals import post_save
import re

from puzzles.ejabberd import ejabberdctl
from puzzles.googlespreadsheet import create_google_spreadsheet

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

class PuzzleWrongAnswer(models.Model):
    puzzle = models.ForeignKey('Puzzle')
    answer = models.CharField(max_length=200)

    class Meta:
        unique_together = ('puzzle', 'answer')

    def __unicode__(self):
        return 'answer "%s" for puzzle "%s"' % (self.answer, self.puzzle.title)

class Puzzle(models.Model):
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
        # Save first, so that we don't create a new spreadsheet if the
        # save would fail.
        super(Puzzle, self).save(*args, **kwargs)

        if self.spreadsheet == '':
            self.spreadsheet = create_google_spreadsheet(self.title)
            # create() uses force_insert, override that here.
            kwargs['force_update'] = True
            kwargs['force_insert'] = False
            super(Puzzle, self).save(*args, **kwargs)

class TagList(OrderedModel):
    name = models.CharField(max_length=200, unique=True)
    tags = models.ManyToManyField('Tag')

    def __unicode__(self):
        return self.name

class UserProfile(models.Model):
    user = models.OneToOneField(User)

    has_jabber_account = models.BooleanField()

def jabber_username(user):
    first = ''.join(re.findall("\w", user.first_name))
    last = ''.join(re.findall("\w", user.last_name))
    return first + '.' + last[0:1]

def jabber_host():
    return 'metaphysical.no-ip.org'

_jabber_password = None
def jabber_password():
    global _jabber_password
    if _jabber_password is None:
        _jabber_password = open('/etc/metaphysical/jabber-password').read()
    return _jabber_password

def create_jabber_user(**kwargs):
    try:
        user = kwargs['instance']
        try:
            user_profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            user_profile = UserProfile.objects.create(user=user, has_jabber_account=False)
        if not user_profile.has_jabber_account and user.first_name != '':
            username = jabber_username(user)
            with ejabberdctl() as e:
                e('register', username, jabber_host(), jabber_password())
                e('set_vcard', username, jabber_host(), 'FN', user.first_name + ' ' + user.last_name)
                e('set_vcard2', username, jabber_host(), 'N', 'FAMILY', user.last_name)
                e('set_vcard2', username, jabber_host(), 'N', 'GIVEN', user.first_name)
                e('push_alltoall', jabber_host(), 'Puzzlers')
            user_profile.has_jabber_account = True
            user_profile.save()
    except Exception, e:
        import traceback
        traceback.print_exc()

post_save.connect(create_jabber_user, sender=User)
