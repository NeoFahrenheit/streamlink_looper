import streamlink
from wx import CallAfter
from threading import Thread
import download_thread as dt
from pubsub import pub
from datetime import datetime
from urllib.parse import urlparse
from enums import ID

class Scheduler(Thread):
    def __init__(self, parent, appData):
        Thread.__init__(self)

        self.session = streamlink.Streamlink()
        self.isActive = False
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

    def run(self):
        ''' Starts this thread's activity. '''

        self.isActive = True
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

        # We check first how the wait is for everybody.
        for queue in self.scheduler:
            for streamer in queue['streamers']:
                waited = streamer['waited']
                limit = queue['wait_time'] * 3 * streamer['priority']
                streamer['waited'] = waited - limit

            # Now we need the one who waited more.
            queue['streamers'].sort(reverse=True, key=lambda x: x['waited'])

        queue_index = 0
        for queue in self.scheduler:
            if queue['domain'] == domain:
                break
            else:
                queue_index += 1
                                
        index = -1
        i = 0

        queue = self.scheduler[queue_index]
        for streamer in queue['streamers']:
            if streamer['wait_until'] != '':
                i += 1
                continue
            else:
                index = i
                break

        if index < 0:
            return

        streamer_dict = self.scheduler[queue_index]['streamers'][index]
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
                queue_domain['streamers'].append(streamer)

    def OnTimer(self):
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
        ''' pubsub('scheduler-edit) -> A streamer has been edit though the setings menu. This function
        changes the `self.scheduler` in the scheduler. If this stremaer thread is active, the changes will
        remain unchanged there. '''

        for i in range(0, len(self.scheduler)):
            if self.scheduler[i]['name'] == oldName:
                self.scheduler[i]['name'] = inData['name']
                self.scheduler[i]['url'] = inData['url']
                self.scheduler[i]['priority'] = inData['priority']
                self.scheduler[i]['quality'] = inData['quality']

                CallAfter(pub.sendMessage, topicName='edit-in-tree', oldName=oldName, newName=inData['name'])  
                return

    def TransferFromFridgeToQueue(self, name: str):
        """ Gives a empty string value to the 'wait_until' key on the queue and the file. """

        for i in range(0, len(self.scheduler)):
            if self.scheduler[i]['name'] == name:
                self.scheduler[i]['wait_until'] = ''

        for i in range(0, len(self.appData['streamers_data'])):
            if self.appData['streamers_data'][i]['name'] == name:
                self.appData['streamers_data'][i]['wait_until'] = ''
                pub.sendMessage('save-file')