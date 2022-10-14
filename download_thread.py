import os
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

    def __init__(self, url, name, dir):
        Thread.__init__(self)
        self.isActive = True
        self.url = url
        self.name = name
        self.dir = dir
        self.c = 0

        self.stopwatch = stopwatch.StopWatch()
        self.dl_total = 0
        self.dl_temp = 0
        self.last_part = 0
        self.j = 0
        self.m3u8_obj = None

    def run(self):
        ''' Runs the thread. '''

        pub.subscribe(self.OnTimer, 'ping-timer')

        now = datetime.now()
        time = now.strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{self.name}_{time}"
        file = open(f"{self.dir}/{filename}.ts", "wb")

        while self.fetch_stream() and self.isActive:
            # I don't understand the for i in range() below or why we need the self.j.
            for i in range(self.j - 1, 0, -1):
                with requests.get(self.m3u8_obj.segments[-i].uri) as r:
                    for chunk in r.iter_content():
                        self.dl_total += len(chunk)
                        self.dl_temp += len(chunk)
                        file.write(chunk)

        file.close()

        # Changing the container of the stream to .mp4. This should be very fast.
        ts = f"{self.dir}/{filename}.ts"
        mp4 = f"{self.dir}/{filename}.mp4"
        subprocess.call(["ffmpeg", "-y", "-i", ts, "-vcodec", "copy", "-acodec", "copy", "-map", "0:v", "-map", "0:a", mp4])
        os.remove(f"{self.dir}/{filename}.ts")
        pub.unsubAll()

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
            if self.m3u8_obj.segments[
                    -self.j].program_date_time == previous_part_time:
                break

        return True

    def OnTimer(self):
        ''' Called every second. '''

        self.c += 1
        if self.c == 10:
            self.isActive = False

        self.stopwatch.ping()

        watch, size, speed = util.get_progress_text(self.stopwatch, self.dl_total, self.dl_temp)
        CallAfter(pub.sendMessage, topicName='update-download-info', name=self.name, watch=watch, size=size, speed=speed)
        self.dl_temp = 0
