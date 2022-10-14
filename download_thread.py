from wx import CallAfter
import streamlink
import requests
import subprocess
import m3u8
from pubsub import pub
from threading import Thread
import stopwatch
import utilities as util


class Download(Thread):

    def __init__(self, url, name, dir):
        Thread.__init__(self)
        self.url = url
        self.name = name
        self.dir = dir

        self.stopwatch = stopwatch.StopWatch()
        self.dl_total = 0
        self.dl_temp = 0
        self.last_part = 0
        self.j = 0
        self.m3u8_obj = None

    def run(self):
        ''' Runs the thread. '''

        pub.subscribe(self.OnTimer, 'ping-timer')
        filename = self.url.split('/')[-1]
        file = open(f"{self.dir}/{filename}.ts", "wb")

        while self.fetch_stream():
            # I don't understand the for i in range() below or why we need the self.j.
            for i in range(self.j - 1, 0, -1):
                with requests.get(self.m3u8_obj.segments[-i].uri) as r:
                    for chunk in r.iter_content():
                        self.dl_total += len(chunk)
                        self.dl_temp += len(chunk)
                        file.write(chunk)

        file.close()
        # Changing the container of the stream to .mp4. This should be very fast.
        subprocess.call(
            f"ffmpeg -y -i {filename + '.ts'} -vcodec copy -acodec copy -map 0:v -map 0:a {filename}.mp4"
        )
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
        self.stopwatch.ping()
        # util.print_progress_text(self.stopwatch, self.dl_total, self.dl_temp)
        self.dl_temp = 0
