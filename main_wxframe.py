import subprocess
import os
import wx
import wx.richtext as rt
from pubsub import pub
import json
from scheduler import Scheduler
import stopwatch
import settings

class MainFrame(wx.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.SetTitle('Streamlink Lopper')
        self.SetSize(800, 400)
        self.version = 0.1
        self.appData = {}
        self.scheduler = []

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer)
        self.timer.Start(1000)

        self.LoadJsonFile()
        self.InitUI()
        self.CenterOnScreen()

        pub.subscribe(self.SaveFile, 'save-file')

    def LoadJsonFile(self) -> None:
        ''' Loads the .json configuration file. '''

        home = os.path.expanduser('~')
        if not os.path.isfile(f'{home}/.streamlink_looper.json'):
            proc = subprocess.run('streamlink --version', stdout=subprocess.PIPE, text=True)
            streamlink_version = proc.stdout.split()[1]
            self.appData['app_version'] = self.version
            self.appData['streamlink_version'] = streamlink_version
            self.appData['download_dir'] = f"{home}/Videos"
            self.appData['streamers_data'] = []

            with open(f'{home}/.streamlink_looper.json', 'w') as f:
                json.dump(self.appData, f, indent=4)

        else:
            with open(f'{home}/.streamlink_looper.json', 'r', encoding='utf-8') as f:
                text = f.read()
                self.appData = json.loads(text)

    def SaveFile(self) -> None:
        ''' Saves self.appData to json. '''

        home = os.path.expanduser('~')
        with open(f'{home}/.streamlink_looper.json', 'w') as f:
                json.dump(self.appData, f, indent=4)

    def InitUI(self):
        ''' Initializes the GUI. '''

        self.InitMenu()

        self.panel = wx.Panel(self)
        master = wx.BoxSizer(wx.HORIZONTAL)
        looperSizer = wx.BoxSizer(wx.VERTICAL)

        self.rt = rt.RichTextCtrl(self.panel, -1, style=wx.TE_READONLY)
        self.rt.GetCaret().Hide()

        master.Add(looperSizer, proportion=1)
        master.Add(self.rt, proportion=1, flag=wx.ALL | wx.EXPAND, border=5)

        looperSizer.Add(self.GetStreamerSizer('iggiedraws'), proportion=1, flag=wx.EXPAND | wx.ALL, border=15)

        self.panel.SetSizerAndFit(master)

    def InitMenu(self):
        menu = wx.MenuBar()
        file = wx.Menu()

        settings = file.Append(-1, 'Settings')
        file.AppendSeparator()
        exit = file.Append(-1, 'Exit')

        self.Bind(wx.EVT_MENU, self.OnSettings, settings)

        menu.Append(file, 'File')
        self.SetMenuBar(menu)

    def GetStreamerSizer(self, streamer_name: str) -> wx.BoxSizer:
        ''' Returns a Horizontal Sizer about a specific streamer. '''

        sizer = wx.BoxSizer(wx.HORIZONTAL)

        textSize = (125, 23)
        name = wx.StaticText(self.panel, -1, streamer_name, size=textSize)
        self.clock = wx.StaticText(self.panel, -1, '00:00:00', size=textSize, style=wx.ALIGN_CENTER)
        size_speed = wx.StaticText(self.panel, -1, '1.3GiB\t 812 KB/s', size=textSize, style=wx.ALIGN_RIGHT)

        sizer.Add(name, flag=wx.EXPAND)
        sizer.Add(self.clock, flag=wx.EXPAND)
        sizer.Add(size_speed, flag=wx.EXPAND)

        return sizer

    def OnSettings(self, event) -> None:
        # frame = settings.Settings(self, self.appData)
        # frame.ShowModal()

        frame = Scheduler(self, self.appData)

    def OnTimer(self, event):
        ''' Called every second. '''

        pub.sendMessage('ping-timer')