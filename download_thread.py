import os
import sys
from wx import CallAfter
import streamlink
import requests
import subprocess
import m3u8
from pubsub import pub
from threading import Thread
import stopwatch
import utilities as util
from datetime import datetime

class Download(Thread):

    def __init__(self, streamer: dict, dir):
        Thread.__init__(self)
        self.isActive = True
        self.streamer = streamer
        self.url = streamer['url']
        self.name = streamer['name']
        self.dir = dir

        self.dl_total = 0
        self.dl_temp = 0
        self.last_part = 0
        self.j = 0
        self.m3u8_obj = None

    def run(self):
        ''' Runs the thread. '''
        
        self.stopwatch = stopwatch.StopWatch()
        pub.subscribe(self.KillDownloadThread, 'kill-download-threads')

        now = datetime.now()
        time_started = now.strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{self.name}_{time_started}"
        file = open(f"{self.dir}/{filename}.ts", "wb")

        pub.subscribe(self.OnTimer, 'ping-timer')
        while self.fetch_stream() and self.isActive:
            # I don't understand the for i in range() below or why we need the self.j.
            for i in range(self.j - 1, 0, -1):
                with requests.get(self.m3u8_obj.segments[-i].uri) as r:
                    for chunk in r.iter_content():
                        self.dl_total += len(chunk)
                        self.dl_temp += len(chunk)
                        file.write(chunk)

        file.close()
        CallAfter(pub.sendMessage, topicName='delete-panel', name=self.name)

        now = datetime.now()
        time_ended = now.strftime("%H:%M:%S")
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
            streams = streamlink.streams(self.url)
            stream_url = streams["best"]
        except streamlink.NoPluginError:
            print('This website is not supported')
            return False
        except streamlink.PluginError:
            print('The stream is offline or has endend')
            return False
        except streamlink.StreamlinkError:
            print('An error has occurred.')
            return False
        except:
            return False

        self.m3u8_obj = m3u8.load(stream_url.args['url'])

        previous_part_time = self.last_part
        self.last_part = self.m3u8_obj.segments[-1].program_date_time

        for self.j in range(1, len(self.m3u8_obj.segments)):
            if self.m3u8_obj.segments[-self.j].program_date_time == previous_part_time:
                break

        return True

    def OnTimer(self):
        ''' Called every second. '''

        self.stopwatch.ping()

        watch, size, speed = util.get_progress_text(self.stopwatch, self.dl_total, self.dl_temp)
        CallAfter(pub.sendMessage, topicName='update-download-info', name=self.name, watch=watch, size=size, speed=speed)
        self.dl_temp = 0

    def KillDownloadThread(self):
        ''' Sets the `self.isActive` to False to end this thread. '''

        self.isActive = False