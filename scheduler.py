import wx
from pubsub import pub

class Scheduler(wx.Frame):
    def __init__(self, parent, appData):
        super().__init__(parent)
        self.appData = appData
        self.queue = []
        self.wait_time = 15
        self.sec = 0
        self.count = 0

        self.choosen = []

        self.PrepareData()
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer)
        self.timer.Start(10)

    def PrepareData(self):
        for data in self.appData['streamers_data']:
            dic = {}
            dic['name'] = data['name']
            dic['priority'] =  data['priority']
            dic['waited'] = 0
            dic['over_wait'] = 0

            self.queue.append(dic)

            self.choosen.append({'name': dic['name'], 'choosen': 0})

    def ChooseOne(self):
        tmp_queue = []

        # We check first how's the wait is for everybody.
        for data in self.queue:
            waited = data['waited']
            limit = self.wait_time * 3 * data['priority']
            tmp_queue.append(waited - limit)

        # Now we need the one who waited more.
        waited_most = -999
        index = -1
        for i in range (0, len(tmp_queue)):
            if tmp_queue[i] > waited_most:
                index = i
                waited_most = tmp_queue[i]

        self.choosen[index]['choosen'] += 1
        self.queue[index]['waited'] = 0 

    def OnTimer(self, event):
        self.sec += 1
        self.count += 1

        if self.count == 2000:
            print(self.choosen)
            exit(0)

        for data in self.queue:
            data['waited'] += 1

        if self.sec == self.wait_time:
            self.sec = 0
            self.ChooseOne()
            