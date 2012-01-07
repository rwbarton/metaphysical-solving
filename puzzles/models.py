from django.db import models

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
        unique_together = ("taglist", "order")

class Motd(models.Model):
    motd = models.TextField()
