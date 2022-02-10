# Generated by Django 4.0.1 on 2022-02-03 18:34

from django.db import migrations

def makeDefaults(apps,schema_editor):
    Location = apps.get_model("puzzles","Location")
    TagList = apps.get_model("puzzles","TagList")
    Status = apps.get_model("puzzles","Status")
    Priority = apps.get_model("puzzles","Priority")
    Tag = apps.get_model("puzzles","Tag")
    Config = apps.get_model("puzzles","Config")
    
    default_statuses = [('not a puzzle', 'not-puzzle',0),
                        ('not started', 'not-started',1),
                        ('being worked on', 'being-worked',2),
                        ('we got this!', 'got-this',3),
                        ('needs insight', 'needs-insight',4),
                        ('needs bodies', 'needs-bodies',5),
                        ('needs extraction', 'needs-extraction',6),
                        ('currently impuzzlable', 'currently-impuzzlable',7),
                        ('solved!', 'solved',8),
                        ('abandoned', 'abandoned',9)]
    Status.objects.all().delete()
    for status_text, status_css_name, status_order in default_statuses:
        Status(text=status_text, css_name=status_css_name, order=status_order).save()
        
    default_priorities = [('low', 'low',0),
                          ('normal', 'normal',1),
                          ('high', 'high',2),
                          ('asap!', 'asap',3)]
    Priority.objects.all().delete()
    for priority_text, priority_css_name, priority_order in default_priorities:
        Priority(text=priority_text, css_name=priority_css_name, order=priority_order).save()

    default_tags = [('testing',0),
                    ('meta',1),
                    ('unsolved puzzles in solved rounds',2)]
    Tag.objects.all().delete()
    for tag_name, tag_order in default_tags:
        Tag(name=tag_name,order=tag_order).save()

    default_taglists = [('Unsolved Rounds',0),
                        ('All',1)]
    TagList.objects.all().delete()
    for taglist_name, taglist_order in default_taglists:
        TagList(name=taglist_name,order=taglist_order).save()

    ur_taglist = TagList.objects.get(name='Unsolved Rounds')
    ur_taglist.tags.set([Tag.objects.get(name='meta'),
                         Tag.objects.get(name='unsolved puzzles in solved rounds')])
    ur_taglist.save()

    testing_taglist = TagList.objects.get(name='all')
    testing_taglist.tags.set([Tag.objects.get(name='testing')])
    testing_taglist.save()

    default_locations = [('Cambridge',0), ('remote',1), ('unknown',2)]
    Location.objects.all().delete()
    for location_name, location_order in default_locations:
        Location(name=location_name,order=location_order).save()

    Config(default_status=Status.objects.get(text='not started'),
           default_priority=Priority.objects.get(text='normal'),
           default_tag=Tag.objects.get(name='testing'),
           default_taglist=TagList.objects.get(name='Unsolved Rounds'),
           motd='Welcome to the Metaphysical Mystery Tour!'
    ).save()


class Migration(migrations.Migration):

    dependencies = [
        ('puzzles', '0001_squashed_0002_location_userzulipstatus_userprofile_uploadedfile_and_more'),
    ]

    operations = [
        migrations.RunPython(makeDefaults)
    ]