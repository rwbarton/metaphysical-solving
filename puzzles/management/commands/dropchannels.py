from django.core.management.base import BaseCommand
import zulip
import re
from time import sleep

class Command(BaseCommand):
    help = "Archive all Zulip channels devoted to puzzles."

    def add_arguments(self, parser):
        parser.add_argument('--yes',type=str)

    def handle(self, *args, **kwargs):
        if not kwargs['yes']:
            print("WARNING: This will archive all the zulip channels devoted to puzzles.\nIf you really want to do this, use the --yes i-am-sure flag")
            return
        if kwargs['yes']!='i-am-sure':
            print("string argument must be 'i-am-sure'")
            return


        client = zulip.Client(config_file="/etc/puzzle/zulip/zuliprc-admin")


        all_streams = client.get_streams()['streams']
        print('Deleting:')
        for stream in all_streams:
            if re.match(r'^p[0-9]*$',stream['name']):
                print("#%3d: '%s'"%(stream['stream_id'],stream['name']))
                client.delete_stream(stream['stream_id'])
                sleep(0.25)

        channels_to_clean = ['general', 'status', 'what-next']
        for channel_name in channels_to_clean:
            print('Cleaning channel %s'%channel_name)
            response = client.get_messages({'anchor':'newest',
                                            'num_before':5000,
                                            'num_after':0,
                                            'narrow':[{'operator':'channel','operand':channel_name}]})
            if response['result']=='success':
                for message in response['messages']:
                    client.delete_message(message['id'])
                    sleep(0.25)


