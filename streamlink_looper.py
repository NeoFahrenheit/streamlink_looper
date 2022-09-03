import os
import sys

class StreamlinkLooper():
    def __init__(self):
        self.count = 1
        self.arg = sys.argv[1]

        self.get_streamer_name()
        self.get_modified_command()
        self.start_looping()

    def get_streamer_name(self):
        arg = self.arg
        self.streamer_name = arg.split('twitch.tv/')[1].split(' ')[0]

    def get_modified_command(self):
        filename = self.arg.split(' ')[-1]
        mod_filename = f'{self.count}_{self.streamer_name}.mp4'
        self.command = f'{self.arg.split("-o")[0]}-o {mod_filename}'

    def start_looping(self):
        while (True):
            self.get_modified_command()
            os.system(f'cmd /c {self.command}')
            self.count += 1

classObj = StreamlinkLooper()