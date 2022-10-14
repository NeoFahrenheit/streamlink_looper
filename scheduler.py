from wx import CallAfter
from threading import Thread
import download_thread as dt
from pubsub import pub
from datetime import datetime

class Scheduler(Thread):
    def __init__(self, appData):
        Thread.__init__(self)
        self.is_Active = True

        self.threads = []
        self.queue = []
        self.sec = 0
        self.wait_time = appData['wait_time']
        self.dir = appData['download_dir']

        self.PrepareData(appData)
        self.start()

    def run(self):
        self.ChooseOne()
        pub.subscribe(self.OnTimer, 'ping-timer')

    def PrepareData(self, data: dict):
        ''' Prepares the data for the scheduler. Everybody gets their wait time. 
        The closest the wait_time reaches or surpasses the limit `(wait_time * 3 * priority)`, the streamer
        becomes more prioritized to be checked for availability. When the streamer gets checked,
        their wait_time is set to zero.
        '''

        for data in data['streamers_data']:
            dic = {}
            dic['url'] = data['url']
            dic['name'] = data['name']
            dic['priority'] =  data['priority']
            dic['waited'] = 0

            self.queue.append(dic)

            # self.choosen.append({'name': dic['name'], 'choosen': 0}) # For debug only

    def ChooseOne(self):
        ''' Chooses one stream from queue to be checked. '''

        wait_line = []

        # We check first how's the wait is for everybody.
        for data in self.queue:
            waited = data['waited']
            limit = self.wait_time * 3 * data['priority']
            wait_line.append(waited - limit)

        # Now we need the one who waited more.
        waited_most = -999
        index = -1
        for i in range (0, len(wait_line)):
            if wait_line[i] > waited_most:
                index = i
                waited_most = wait_line[i]
        
        is_live = self.CheckStreamer(self.queue[index])
        # We need to be careful. When we removed from the queue, our index
        # is no longer valid. It should be done last.
        if is_live:
            #self.AddStreamerToScrolled(streamer)
            CallAfter(self.AddToLog, self.queue[index]['name'], is_live)
            self.RemoveFromQueue(self.queue[index]['name'])

        else:
            self.queue[index]['waited'] = 0
            CallAfter(self.AddToLog, self.queue[index]['name'], is_live)

    def CheckStreamer(self, streamer: dict) -> bool:
        ''' Checks if a streamer is online. If so, starts it's download thread and append 
        it to `self.threads`. '''

        print(f"Cheking streamer {streamer['name']} for it's status...")
        t = dt.Download(streamer['url'], streamer['name'], self.dir)

        if t.fetch_stream():
            t.start()
            self.threads.append(t)
            return True

        else:
            return False

    def RemoveFromQueue(self, name: str):
        print(f"Removing {name} from queue...")

        for i in range (0, len(self.queue)):
            if self.queue[i]['name'] == name:
                del self.queue[i]
                return

    def AddToQueue(self, streamer: dict):
        d = {}
        d['name'] = streamer['name']
        d['priority'] = streamer['priority']
        d['waited'] = 0

        self.queue.index(len(self.queue), d)

    def OnTimer(self):
        if not self.is_Active:
            pub.unsubAll()
            return

        self.sec += 1
        for data in self.queue:
            data['waited'] += 1

        if self.sec == self.wait_time:
            self.sec = 0
            self.ChooseOne()

    def AddToLog(self, name: str, status: bool):
        ''' Adds to the log on the main window. '''

        now = datetime.now()
        time = now.strftime("%H:%M:%S")
        pub.sendMessage('log', streamer=name, time=time, status=status)

    def AddStreamerToScrolled(self, streamer: dict):
        CallAfter(pub.sendMessage, 'add-streamer', streamer=streamer)