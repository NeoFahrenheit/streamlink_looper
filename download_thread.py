import os
import time
import sys
from wx import CallAfter
import subprocess
from pubsub import pub
from threading import Thread
import stopwatch
import utilities as util

class Download(Thread):

    def __init__(self, streamer: dict, dir: str, session):
        Thread.__init__(self)
        self.isActive = True
        self.session = session

        self.stream_data = None
        self.streamer = streamer
        self.url = streamer['url']
        self.name = streamer['name']
        self.dir = dir

        self.dl_total = 0
        self.dl_temp = 0

    def run(self):
        ''' Runs the thread. '''
        
        self.stopwatch = stopwatch.StopWatch()
        pub.subscribe(self.KillDownloadThread, 'kill-download-threads')

        time_started = time.strftime("%Y-%m-%d__%H-%M-%S")
        filename = f"{self.name}_{time_started}"

        pub.subscribe(self.OnTimer, 'ping-timer')
        self.start_download(filename)
        CallAfter(pub.sendMessage, topicName='delete-panel', name=self.name)

        time_ended = time.strftime("%H-%M-%S")
        CallAfter(pub.sendMessage, topicName='log-stream-ended', streamer=self.name, time=time_ended)

        # Changing the container of the stream to .mp4. This should be very fast.
        ts = f"{self.dir}/{filename}.ts"
        mp4 = f"{self.dir}/{filename}.mp4"

        subprocess.call(["ffmpeg", "-y", "-i", ts, "-vcodec", "copy", "-acodec", "copy", "-map", "0:v", "-map", "0:a", mp4], 
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.remove(ts)

        pub.sendMessage('add-to-queue', streamer=self.streamer)
        sys.exit()

    def fetch_stream(self) -> bool:
        ''' Check if a stream is online. If so, populates crucial variables and returns True. '''

        # Will this catch streams end or stream offline? What about hostings? We don't want that.
        try:
            streams = self.session.streams(self.url)
            self.stream_data = streams["best"].open()
        except:
            return False

        return True

    def start_download(self, filename: str):
        file = open(f"{self.dir}/{filename}.ts", "ab+")
 
        start = time.perf_counter()
        data = self.stream_data.read(1024)

        while data:
            self.dl_total += len(data)
            self.dl_temp += len(data)
            
            diff = time.perf_counter() - start
            if diff > 1:
                size, speed = util.get_progress_text(self.dl_total, self.dl_temp, diff)
                start = time.perf_counter()

                CallAfter(pub.sendMessage, topicName='update-download-info', name=self.name, watch=None, size=size, speed=speed)
                self.dl_temp = 0

            file.write(data)
            data = self.stream_data.read(1024)
        file.close()


    def OnTimer(self):
        ''' Called every second. '''

        self.stopwatch.ping()
        CallAfter(pub.sendMessage, topicName='update-download-info', 
        name=self.name, watch=self.stopwatch.to_str(), size=None, speed=None)

    def KillDownloadThread(self):
        ''' Sets the `self.isActive` to False to end this thread. '''

        self.isActive = False