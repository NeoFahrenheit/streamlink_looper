import os
import wx
import wx.richtext as rt
import wx.lib.scrolledpanel as scrolled
import subprocess
from pubsub import pub
import json
from scheduler import Scheduler
import settings
import utilities

class MainFrame(wx.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.STREAMER_COLOR = '#a970ff'
        self.STATUS_ON_COLOR = '#46734d'
        self.STATUS_OFF_COLOR = '#cc3535'
        self.ID = utilities.ID()

        self.SetTitle('Streamlink Lopper')
        self.SetSize(800, 400)
        self.scheduler_status = 'Stopped'
        self.status_bar = self.CreateStatusBar()

        self.version = 0.1
        self.appData = {}
        self.scheduler = []
        self.scheduler_thread = None

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer)
        self.timer.Start(1000)

        self.LoadJsonFile()
        self.InitUI()
        self.CenterOnScreen()

        pub.subscribe(self.SaveFile, 'save-file')
        pub.subscribe(self.Log, 'log')
        pub.subscribe(self.AddStreamer, 'add-streamer')

    def LoadJsonFile(self) -> None:
        ''' Loads the .json configuration file. '''

        home = os.path.expanduser('~')
        if not os.path.isfile(f'{home}/.streamlink_looper.json'):
            proc = subprocess.run('streamlink --version', stdout=subprocess.PIPE, text=True)
            streamlink_version = proc.stdout.split()[1]
            self.appData['app_version'] = self.version
            self.appData['streamlink_version'] = streamlink_version
            self.appData['download_dir'] = f"{home}/Videos"
            self.appData['wait_time'] = 15
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
        self.scrolledSizer = wx.BoxSizer(wx.VERTICAL)

        self.scrolled = scrolled.ScrolledPanel(self.panel, -1, style=wx.SUNKEN_BORDER)
        self.scrolled.SetSizer(self.scrolledSizer)

        self.rt = rt.RichTextCtrl(self.panel, -1, style=wx.TE_READONLY)
        self.rt.GetCaret().Hide()

        master.Add(self.scrolled, proportion=1)
        master.Add(self.rt, proportion=1, flag=wx.ALL | wx.EXPAND, border=5)

        self.panel.SetSizerAndFit(master)

    def InitMenu(self):
        menu = wx.MenuBar()
        file = wx.Menu()
        self.scheduler_menu = wx.Menu()
        streamers = wx.Menu()

        settings = file.Append(-1, 'Settings', 'Open settings menu.')
        file.AppendSeparator()
        exit = file.Append(-1, 'Exit', 'Exit the software')

        start = self.scheduler_menu.Append(-1, 'Start', 'Start the scheduler')
        pause = self.scheduler_menu.Append(-1, 'Pause', 'Pause the scheduler')
        stop = self.scheduler_menu.Append(-1, 'Stop', 'Stop the scheduler')
        
        users = [name['name'] for name in self.appData['streamers_data']]
        for name in users:
            streamers.Append(-1, name, f"Check if {name} is online now.")

        self.scheduler_menu.Append(self.ID.SCHEDULER, 'Check now...', streamers)
        self.scheduler_menu.Enable(self.ID.SCHEDULER, False)

        self.Bind(wx.EVT_MENU, self.OnSettings, settings)
        self.Bind(wx.EVT_MENU, self.OnStart, start)

        menu.Append(file, 'File')
        menu.Append(self.scheduler_menu, 'Scheduler')
        self.SetMenuBar(menu)

    def GetStreamerSizer(self, streamer: str) -> wx.BoxSizer:
        ''' Returns a Horizontal Sizer about a specific streamer. '''

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        streamer_name = streamer['name']

        textSize = (100, 23)
        name_t = wx.StaticText(self.panel, -1, streamer_name, size=textSize, style=wx.ALIGN_LEFT, name=streamer_name)
        self.clock = wx.StaticText(self.panel, -1, '00:00:00', size=textSize, style=wx.ALIGN_CENTER, name=streamer_name)
        size = wx.StaticText(self.panel, -1, '1.3GiB', size=textSize, style=wx.ALIGN_RIGHT, name=streamer_name)
        speed = wx.StaticText(self.panel, -1, '812 KB/s', size=textSize, style=wx.ALIGN_RIGHT, name=streamer_name)

        sizer.Add(name_t, flag=wx.EXPAND)
        sizer.Add(self.clock, flag=wx.EXPAND)
        sizer.Add(size, flag=wx.EXPAND)
        sizer.Add(speed, flag=wx.EXPAND)
        
        return sizer

    def Log(self, streamer: str, time: str, status: bool):
        ''' Adds to the log on the main window. '''

        self.rt.WriteText("The streamer ") 
        self.WriteStreamerName(streamer)
        self.rt.WriteText(f" was checked at {time} and it was ")
        self.WriteStreamerStatus(status)
        self.rt.WriteText(".\n")

    def WriteStreamerName(self, name: str):

        self.rt.BeginTextColour(self.STREAMER_COLOR)
        self.rt.BeginBold()

        self.rt.WriteText(name)

        self.rt.EndTextColour()
        self.rt.EndBold()

    def WriteStreamerStatus(self, status: bool):
        
        self.rt.BeginBold()

        if status:
            self.rt.BeginTextColour(self.STATUS_ON_COLOR)
            self.rt.WriteText('online')
        else:
            self.rt.BeginTextColour(self.STATUS_OFF_COLOR)
            self.rt.WriteText('offline')
        
        self.rt.EndTextColour()
        self.rt.EndBold()

    def AddStreamer(self, streamer: dict):

        self.scrolledSizer.Add(self.GetStreamerSizer(streamer), proportion=1, flag=wx.EXPAND | wx.ALL, border=15)
        self.scrolled.SendSizeEvent()

    def OnSettings(self, event) -> None:
        frame = settings.Settings(self, self.appData)
        frame.ShowModal()

    def OnStart(self, event):

        if self.scheduler_status != 'Running':
            self.scheduler_thread = Scheduler(self.appData)
            self.scheduler_status = 'Running'
            self.scheduler_menu.Enable(self.ID.SCHEDULER, True)

    def OnTimer(self, event):
        ''' Called every second. '''

        pub.sendMessage('ping-timer')