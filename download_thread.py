import os
import time
import sys
from wx import CallAfter
import subprocess
from pubsub import pub
import json
from threading import Thread
from urllib.parse import urlparse
import stopwatch
import utilities as util
from enums import ID

class Download(Thread):
    def __init__(self, parent, streamer: dict, dir: str, session):
        Thread.__init__(self)

        self.parent = parent
        self.isActive = True
        self.session = session

        self.stream_data = None
        self.streamer = streamer
        self.url = streamer['url']
        self.name = streamer['name']
        self.userQuality = streamer['quality']
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

        time_ended = time.strftime("%H:%M:%S")
        CallAfter(pub.sendMessage, topicName='log-stream-ended', streamer=self.name, time=time_ended)

        if 'audio' not in self.streamerQuality:
            # Changing the container of the stream to .mp4. This should be very fast.
            try:
                ts = f"{self.dir}/{filename}.ts"
                mp4 = f"{self.dir}/{filename}.mp4"

                subprocess.call(["ffmpeg", "-y", "-i", ts, "-vcodec", "copy", "-acodec", "copy", "-map", "0:v", "-map", "0:a", mp4], 
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                os.remove(ts)
            except:
                pass
            
        d = self.GetStreamerFromFile(self.name)
        domain = urlparse(self.url).netloc
        pub.sendMessage('add-to-queue', streamer=d, queue_domain=domain)
        pub.sendMessage('remove-from-thread', name=self.name)

        CallAfter(pub.sendMessage, topicName='remove-from-tree', name=self.name, parent_id=ID.TREE_DOWNLOADING)
        CallAfter(pub.sendMessage, topicName='add-to-tree', name=self.name, parent_id=ID.TREE_QUEUE)

        sys.exit()

    def fetch_stream(self) -> bool:
        ''' Check if a stream is online. If so, populates crucial variables and returns True. '''

        # Will this catch streams end or stream offline? What about hostings? We don't want that.
        try:
            streams = self.session.streams(self.url)
            quality_list = list(streams.keys())
            self.streamerQuality = self.ChooseQuality(self.userQuality, quality_list)
            self.stream_data = streams[self.streamerQuality].open()
        except:
            return False

        return True

    def start_download(self, filename: str):
        file = open(f"{self.dir}/{filename}.ts", "ab+")
        CallAfter(pub.sendMessage, topicName='update-download-info', 
            name=self.name, watch=None, quality=self.streamerQuality, size=None, speed=None)
 
        start = time.perf_counter()
        data = self.stream_data.read(1024)

        while data and self.isActive:
            self.dl_total += len(data)
            self.dl_temp += len(data)
            
            diff = time.perf_counter() - start
            if diff > 1:
                size, speed = util.get_progress_text(self.dl_total, self.dl_temp, diff)
                start = time.perf_counter()

                CallAfter(pub.sendMessage, topicName='update-download-info', name=self.name, watch=None, quality=None, size=size, speed=speed)
                self.dl_temp = 0

            file.write(data)
            data = self.stream_data.read(1024)
        file.close()


    def OnTimer(self):
        ''' Called every second. '''

        self.stopwatch.ping()
        CallAfter(pub.sendMessage, topicName='update-download-info', 
        name=self.name, watch=self.stopwatch.to_str(), quality=None, size=None, speed=None)

    def KillDownloadThread(self):
        ''' Sets the `self.isActive` to False to end this thread. '''

        self.isActive = False

    def ChooseQuality(self, quality: str, q_list: list) -> str:
        ''' Given a `quality`, chooses the apropriate quality available in `q_list`.
        Returns the exact quality chosen. '''
        
        q_list_sorted = []
        for q in q_list:
            if 'p' in q:
                res = q.split('p')[0]
                q_list_sorted.append(int(res))
            else:
                q_list_sorted.append(q)

        index = -1

        if quality == 'audio only':
            for v in q_list_sorted:
                if isinstance(v, str) and 'audio' in v:
                    return v

            quality = 'worst'

        # Discoverin exactly what the best or worst are.
        value = -1
        if quality == 'best':
            for i in range (0, len(q_list_sorted)):
                if isinstance(q_list_sorted[i], int) and q_list_sorted[i] >= value:
                    value = q_list_sorted[i]
                    index = i

            return q_list[index]

        value = 9999
        if quality == 'worst':
            for i in range (0, len(q_list_sorted)):
                if isinstance(q_list_sorted[i], int) and q_list_sorted[i] <= value:
                    value = q_list_sorted[i]
                    index = i

            return q_list[index]

        resolution = 0
        match quality:
            case 'high':
                resolution = 720
            case 'medium':
                resolution = 480
            case 'low':
                resolution = 240
            case _:
                resolution = 1080

        index = -1
        for i in range(0, len(q_list_sorted)):
            if isinstance(q_list_sorted[i], int):
                value = q_list_sorted[i]
            else:
                continue

            if value <= resolution:
                index = i

        return q_list[index]

    def GetStreamerFromFile(self, name: str) -> dict:
        ''' Search the app file, the dictionary from the streamer `name`. 
        Getting this info through the file is necessary if the user edited the streamer
        while he or she was live. '''

        home = os.path.expanduser('~')
        with open(f'{home}/.streamlink_looper.json', 'r', encoding='utf-8') as f:
            text = f.read()
            appData = json.loads(text)

        for s in appData['streamers_data']:
            if s['name'] == name:
                return s

        return None