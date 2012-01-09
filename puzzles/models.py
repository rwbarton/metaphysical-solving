from django.db import models

from django.contrib.auth.models import User
from django.db.models.signals import post_save
import re

from puzzles.ejabberd import ejabberdctl

class Status(models.Model):
    text = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    sort_order = models.PositiveIntegerField(unique=True)

    class Meta:
        ordering = ['sort_order']

        verbose_name_plural = 'statuses'

    def __unicode__(self):
        return self.text

class Priority(models.Model):
    text = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    sort_order = models.PositiveIntegerField(unique=True)

    class Meta:
        ordering = ['sort_order']

        verbose_name_plural = 'priorities'

    def __unicode__(self):
        return self.text

class Tag(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __unicode__(self):
        return self.name

class PuzzleWrongAnswer(models.Model):
    puzzle = models.ForeignKey('Puzzle')
    answer = models.CharField(max_length=200)

class Puzzle(models.Model):
    title = models.CharField(max_length=200)
    url = models.URLField()

    status = models.ForeignKey('Status')
    priority = models.ForeignKey('Priority')
    tags = models.ManyToManyField('Tag', blank=True)

    spreadsheet = models.URLField(blank=True)
    answer = models.CharField(max_length=200, blank=True)

    def __unicode__(self):
        return self.title

class TagList(models.Model):
    name = models.CharField(max_length=200, unique=True)
    tags = models.ManyToManyField('Tag', through='TagTagListRelation')

    def __unicode__(self):
        return self.name

class TagTagListRelation(models.Model):
    tag = models.ForeignKey('Tag')
    taglist = models.ForeignKey('TagList')
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ['taglist', 'order']
        unique_together = ("taglist", "order")

class Motd(models.Model):
    motd = models.TextField(blank=True)

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
