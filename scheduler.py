import streamlink
from wx import CallAfter
from threading import Thread
import download_thread as dt
from pubsub import pub
from datetime import datetime
from enums import ID

class Scheduler(Thread):
    def __init__(self, parent, appData):
        Thread.__init__(self)

        self.session = streamlink.Streamlink()
        self.isActive = False
        self.parent = parent

        self.threads = []
        self.queue = []
        self.sec = 0
        self.wait_time = appData['wait_time']
        self.dir = appData['download_dir']

        self.PrepareData(appData)

    def run(self):
        ''' Starts this thread's activity. '''

        pub.subscribe(self.OnTimer, 'ping-timer')
        pub.subscribe(self.AddToQueue, 'add-to-queue')
        pub.subscribe(self.RemoveFromQueue, 'remove-from-queue')
        pub.subscribe(self.OnEdit, 'scheduler-edit')
        pub.subscribe(self.RemoveFromThread, 'remove-from-thread')

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
            dic['quality'] = data['quality']
            dic['priority'] =  data['priority']
            dic['wait_until'] =  data['wait_until']
            dic['waited'] = 0

            self.queue.append(dic)

    def ChooseOne(self):
        ''' Chooses one stream from queue to be checked. '''

        if not self.queue:
            return

        # We check first how the wait is for everybody.
        for data in self.queue:
            waited = data['waited']
            limit = self.wait_time * 3 * data['priority']
            data['waited'] = waited - limit

        # Now we need the one who waited more.
        self.queue.sort(reverse=True, key=lambda x: x['waited'])
        index = -1

        for i in range(0, len(self.queue)):
            if self.queue[i]['wait_until'] != '':
                continue
            else:
                index = i
                break

        if index < 0:
            return

        is_live = self.CheckStreamer(self.queue[index])
        # We need to be careful. When we removed from the queue, our index
        # is no longer valid. It should be done last.
        if is_live:
            name = self.queue[index]['name']

            CallAfter(self.parent.AddStreamer, self.queue[index])
            CallAfter(self.AddToLog, name, is_live)
            self.RemoveFromQueue(name)
            
            CallAfter(pub.sendMessage, topicName='remove-from-tree', name=name, parent_id=ID.TREE_FRIDGE)  
            CallAfter(pub.sendMessage, topicName='remove-from-tree', name=name, parent_id=ID.TREE_QUEUE)  

        else:
            self.queue[index]['waited'] = 0
            CallAfter(self.AddToLog, self.queue[index]['name'], is_live)

    def CheckStreamer(self, streamer: dict) -> bool:
        ''' Checks if a streamer is online. If so, starts it's download thread. '''

        t = dt.Download(self, streamer, self.dir, self.session)

        if t.fetch_stream():
            t.start()
            self.threads.append(t)
            return True
        else:
            del t
            return False

    def RemoveFromThread(self, name: str) -> bool:
        ''' `pubsub('remove-from-thread')` -> Removes the thread named with corresponding `name` from the self.threads. '''

        for i in range (0, len(self.threads)):
            if self.threads[i].name == name:
                self.threads[i].isActive = False
                del self.threads[i]
                return True

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
        d['quality'] = streamer['quality']
        d['priority'] = streamer['priority']
        d['wait_until'] = streamer['wait_until']
        d['waited'] = 0

        self.queue.append(d)

    def OnTimer(self):
        if not self.isActive:
            return

        self.sec += 1
        # Streamers on the fridge don't get their count increased.
        
        for data in self.queue:
            if data['wait_until'] != '':
                now = datetime.now()
                until = datetime.strptime(data['wait_until'], "%Y-%m-%d %H:%M:%S")

                if now >= until:
                    data['wait_until'] = ''
                    pub.sendMessage('update-wait-until', name=data['wait_until'], date_time=None)

            else:
                data['waited'] += 1

        if self.sec == self.wait_time:
            self.sec = 0
            self.ChooseOne()

    def AddToLog(self, name: str, status: bool):
        ''' Adds to the log on the main window. '''

        now = datetime.now()
        time = now.strftime("%H:%M:%S")
        pub.sendMessage('log', streamer=name, time=time, status=status)

    def OnEdit(self, oldName: str, inData: dict):
        ''' pubsub('scheduler-edit) -> A streamer has been edit though the setings menu. This function
        changes the `self.queue` in the scheduler. If this stremaer thread is active, the changes will
        remain unchanged there. '''

        for i in range(0, len(self.queue)):
            if self.queue[i]['name'] == oldName:
                self.queue[i]['name'] = inData['name']
                self.queue[i]['url'] = inData['url']
                self.queue[i]['priority'] = inData['priority']
                self.queue[i]['quality'] = inData['quality']

                CallAfter(pub.sendMessage, topicName='edit-in-tree', oldName=oldName, newName=inData['name'])  
                return

