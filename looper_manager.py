import os
from threading import Thread

class LooperManager(Thread):
    def __init__(self, streamers: list):
        super().__init__(self)
        self.streamers = streamers

        self.start()

    def parte_streamers(self):
        ''' Parte the streamers, given their priorities. '''

    def run(self):
        # We need to wait a given time to check if a streamer is online.
        # Maybe a list with the streamer commands. Wait for x secs and the check the next one.

        ...

    def start_listening(self, streamers: list[str]):
        for streamer in streamers:
            ...

