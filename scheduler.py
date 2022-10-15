import sys
from wx import CallAfter
from threading import Thread
import download_thread as dt
from pubsub import pub
from datetime import datetime

class Scheduler(Thread):
    def __init__(self, parent, appData):
        Thread.__init__(self)
        self.isActive = True
        self.parent = parent

        self.queue = []
        self.sec = 0
        self.wait_time = appData['wait_time']
        self.dir = appData['download_dir']

        self.PrepareData(appData)
        self.start()

    def run(self):

        self.ChooseOne()
        pub.subscribe(self.OnTimer, 'ping-timer')
        pub.subscribe(self.AddToQueue, 'add-to-queue')
        pub.subscribe(self.KillSchedulerThread, 'kill-scheduler-thread')

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

    def ChooseOne(self):
        ''' Chooses one stream from queue to be checked. '''

        if not self.queue or not self.isActive:
            return

        wait_line = []

        # We check first how's the wait is for everybody.
        for streamer in self.queue:
            waited = streamer['waited']
            limit = self.wait_time * 3 * streamer['priority']
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
            CallAfter(self.parent.AddStreamer, self.queue[index])
            CallAfter(self.AddToLog, self.queue[index]['name'], is_live)
            self.RemoveFromQueue(self.queue[index]['name'])

        else:
            self.queue[index]['waited'] = 0
            CallAfter(self.AddToLog, self.queue[index]['name'], is_live)

    def CheckStreamer(self, streamer: dict) -> bool:
        ''' Checks if a streamer is online. If so, starts it's download thread. '''

        t = dt.Download(streamer, self.dir)

        if t.fetch_stream():
            t.start()
            return True
        else:
            return False

    def RemoveFromQueue(self, name: str):
        ''' Removes a stream from the queue. '''

        for i in range (0, len(self.queue)):
            if self.queue[i]['name'] == name:
                del self.queue[i]
                return

    def AddToQueue(self, streamer: dict):
        ''' Adds a stream to the queue. '''

        d = {}
        d['url'] = streamer['url']
        d['name'] = streamer['name']
        d['priority'] = streamer['priority']
        d['waited'] = 0

        self.queue.append(d)

    def OnTimer(self):
        if not self.isActive:
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

    def KillSchedulerThread(self):
        ''' Sets the `self.isActive` to False to end this thread. '''

        sys.exit()