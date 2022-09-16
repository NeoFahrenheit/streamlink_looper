import os
import sys
import time

class StreamlinkLooper():
    def __init__(self):
        self.arg = sys.argv[1]

        self.get_streamer_name()
        self.get_modified_command()
        self.start_looping()

    def get_streamer_name(self):
        arg = self.arg
        self.streamer_name = arg.split('twitch.tv/')[1].split(' ')[0]

    def get_modified_command(self):
        t = time.localtime()
        now = time.strftime('%Y-%m-%d_%H-%M-%S', t)
        filename = f'{self.streamer_name}_{now}.mp4'
        self.command = f'{self.arg.split("-o")[0]}-o {filename}'

    def start_looping(self):
        while (True):
            self.get_modified_command()
            os.system(f'cmd /c {self.command}')

classObj = StreamlinkLooper()

