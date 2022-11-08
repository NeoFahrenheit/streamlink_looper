import streamlink
from wx import CallAfter
from threading import Thread
import download_thread as dt
from pubsub import pub
from datetime import datetime
from urllib.parse import urlparse
from enums import ID

class Scheduler(Thread):
    def __init__(self, parent, appData: dict, startNow: bool):
        Thread.__init__(self)

        self.session = streamlink.Streamlink()
        self.isActive = startNow
        self.wasOnBefore = False
        self.parent = parent
        self.appData = appData

        self.threads = []
        self.scheduler = []
        self.sec = 0
        self.dir = appData['download_dir']

        self.PrepareData()

        pub.subscribe(self.OnTimer, 'ping-timer')
        pub.subscribe(self.AddToQueue, 'add-to-queue')
        pub.subscribe(self.RemoveFromQueue, 'remove-from-queue')
        pub.subscribe(self.OnEdit, 'scheduler-edit')
        pub.subscribe(self.RemoveFromThread, 'remove-from-thread')
        pub.subscribe(self.UpdateDomainsWaitTime, 'update-domain-wait-time')

        self.start()

    def run(self):
        ''' Starts this thread's activity. '''

        if self.isActive:
            self.ChooseOneFromEachDomain()
            self.wasOnBefore = True

    def Restart(self):
        """ Starts the thread and check if it's the first time it being turned on to choose streams from each domain. """

        self.isActive = True
        if not self.wasOnBefore:
            self.ChooseOneFromEachDomain()

    def ChooseOneFromEachDomain(self):
        """ Choose one streamer to be checked from each domain. """

        if self.isActive:
            for queue in self.scheduler:
                self.ChooseOne(queue['domain'])

    def PrepareData(self):
        ''' Prepares the data for the scheduler. Everybody gets their wait time. 
        The closest the wait_time reaches or surpasses the limit `(wait_time * 3 * priority)`, the streamer
        becomes more prioritized to be checked for availability. When the streamer gets checked,
        their wait_time is set to zero.
        '''

        for domain, wait_time in self.appData['domains'].items():
            dic = {}
            dic['domain'] = domain
            dic['wait_time'] = wait_time
            dic['queue_waited'] = 0
                        
            streamers = []
            for s in self.appData['streamers_data']:
                if urlparse(s['url']).netloc == domain:
                    s_dic = {}
                    s_dic = s
                    s_dic['waited'] = 0
                    streamers.append(s_dic)

            dic['streamers'] = streamers
            self.scheduler.append(dic)

    def ChooseOne(self, domain: str):
        ''' Chooses one stream from `domain` queue to be checked. '''

        if not self.scheduler:
            return
        
        queue_index = 0
        for queue in self.scheduler:
            if queue['domain'] == domain:
                break
            else:
                queue_index += 1

        queue = self.scheduler[queue_index]
        wait_time = queue['wait_time']

        # We check first how the wait is for everybody in the queue.
        wait_queue = []
        i = 0
        for streamer in queue['streamers']:
            waited = streamer['waited']
            limit = wait_time * 3 * streamer['priority']
            wait_queue.append((i, waited - limit))
            i += 1

        # Now we need the one who waited more.
        wait_queue.sort(reverse=True, key=lambda x: x[1])
        
        chosen = -1
        # Choosing the one
        for index in wait_queue:
            i = index[0]
            if queue['streamers'][i]['wait_until'] == '':
                chosen = i
                break

        if chosen < 0:
            return

        streamer_dict = queue['streamers'][chosen]
        is_live = self.CheckStreamer(streamer_dict)

        # We need to be careful. When we removed from the queue, our index
        # is no longer valid. It should be done last.
        if is_live:
            name = streamer_dict['name']

            CallAfter(self.parent.AddStreamer, streamer_dict)
            CallAfter(self.AddToLog, name, is_live)
            self.RemoveFromQueue(name)
            
            CallAfter(pub.sendMessage, topicName='remove-from-tree', name=name, parent_id=ID.TREE_FRIDGE)  
            CallAfter(pub.sendMessage, topicName='remove-from-tree', name=name, parent_id=ID.TREE_QUEUE)  

        else:
            streamer_dict['waited'] = 0
            CallAfter(self.AddToLog, streamer_dict['name'], is_live)


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

    def GetStreamerByName(self, name: str) -> dict | None:
        """ Returns a streamer dictionary. """

        for queue in self.scheduler:
            for streamer in queue['streamers']:
                if streamer['name'] == name:
                    return streamer

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

        for queue in self.scheduler:
            for i in range (0, len(queue['streamers'])):
                if queue['streamers'][i]['name'] == name:
                    del queue['streamers'][i]
                    return

    def AddToQueue(self, streamer: dict, queue_domain: str):
        ''' Adds a stream to the queue. '''

        for queue in self.scheduler:
            if queue['domain'] == queue_domain:
                queue['streamers'].append(streamer)

    def OnTimer(self):
        """ Gets called every second. """

        if not self.isActive:
            return
        
        for queue in self.scheduler:
            queue['queue_waited'] += 1

            for streamer in queue['streamers']:
                if streamer['wait_until'] != '':
                    now = datetime.now()
                    until = datetime.strptime(streamer['wait_until'], "%Y-%m-%d %H:%M:%S")

                    if now >= until:
                        streamer['wait_until'] = ''
                        pub.sendMessage('update-wait-until', name=streamer['wait_until'], date_time=None)

                else:
                    streamer['waited'] += 1

        for queue in self.scheduler:
            if queue['queue_waited'] == queue['wait_time']:
                queue['queue_waited'] = 0
                self.ChooseOne(queue['domain'])

    def AddToLog(self, name: str, status: bool):
        ''' Adds to the log on the main window. '''

        now = datetime.now()
        time = now.strftime("%H:%M:%S")
        pub.sendMessage('log', streamer=name, time=time, status=status)

    def OnEdit(self, oldName: str, inData: dict):
        ''' pubsub('scheduler-edit) -> A streamer has been edit though the setings menu. 
        If this stremaer thread is active, the changes will remain unchanged there. '''

        for queue in self.scheduler:
            for streamer in queue['streamers']:
                if streamer['name'] == oldName:
                    streamer['name'] = inData['name']
                    streamer['url'] = inData['url']
                    streamer['priority'] = inData['priority']
                    streamer['quality'] = inData['quality']

                    CallAfter(pub.sendMessage, topicName='edit-in-tree', oldName=oldName, newName=inData['name'])  
                    return

    def TransferFromFridgeToQueue(self, name: str):
        """ Gives a empty string value to the 'wait_until' key on the queue and the file. """

        for queue in self.scheduler:
            for streamer in queue['streamers']:
                if streamer['name'] == name:
                    streamer['wait_until'] = ''

        for i in range(0, len(self.appData['streamers_data'])):
            if self.appData['streamers_data'][i]['name'] == name:
                self.appData['streamers_data'][i]['wait_until'] = ''
                pub.sendMessage('save-file')

    def UpdateDomainsWaitTime(self):
        """ Updates the wait time for domains. """

        for domain, wait in self.appData['domains'].items():
            for queue in self.scheduler:
                if queue['domain'] == domain:
                    queue['wait_time'] = wait