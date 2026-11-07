from django.core.management.base import BaseCommand, CommandError
from puzzles.models import Config, Status, Priority, Tag, Location

class Command(BaseCommand):
    help = 'Create reasonable default config, locations, priorities etc.'
    def handle(self, *args, **options):
        configs = Config.objects.all()
        if len(configs) > 0:
            raise CommandError("Already have a config, exiting.")

        default_statuses = [('not a puzzle', 'not-puzzle'),
                            ('not started', 'not-started'),
                            ('being worked on', 'being-worked'),
                            ('we got this!', 'we-got-this'),
                            ('needs insight', 'needs-insight'),
                            ('needs bodies', 'needs-bodies'),
                            ('needs extraction', 'needs-extraction'),
                            ('currently impuzzlable', 'currently-impuzzlable'),
                            ('solved!', 'solved'),
                            ('abandoned', 'abandoned')]
        Status.objects.all().delete()
        for status_text, status_css_name in default_statuses:
            Status(text=status_text, css_name=status_css_name).save()

        default_priorities = [('low', 'low'),
                              ('normal', 'normal'),
                              ('high', 'high'),
                              ('asap!', 'asap')]
        Priority.objects.all().delete()
        for priority_text, priority_css_name in default_priorities:
            Priority(text=priority_text, css_name=priority_css_name).save()

        default_tags = ['testing', 'meta', 'crossword', 'list of clues', 'cryptogram',
                        'cryptic', 'duck konundrum', 'music', 'nikoli', 'logic', 'chess',
                        'physical', 'runaround', 'scavenger hunt', 'video game', 'math',
                        'programming', 'science', 'literature', 'pop culture', 'sports',
                        'MIT', 'geography', 'trivia', 'board games', 'word puzzle', 'event',
                        'interaction', 'anagram', 'hintable', 'art', 'history', 'on campus', 'make something']
        Tag.objects.all().delete()
        for tag_name in default_tags:
            Tag(name=tag_name).save()



        default_locations = ['MIT/Cambridge', 'remote', 'unknown']
        Location.objects.all().delete()
        for location_name in default_locations:
            Location(name=location_name).save()

        Config(default_status=Status.objects.get(text='not started'),
               default_priority=Priority.objects.get(text='normal'),
               default_tag=Tag.objects.get(name='testing'),
               motd='Welcome to the Mystery Hunt!'
               ).save()
