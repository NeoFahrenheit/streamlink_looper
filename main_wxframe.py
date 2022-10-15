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
        self.SetSize(1000, 400)
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

        pub.subscribe(self.UpdateDownloadInfo, 'update-download-info')
        pub.subscribe(self.DeletePanel, 'delete-panel')
        pub.subscribe(self.SaveFile, 'save-file')
        pub.subscribe(self.Log, 'log')
        pub.subscribe(self.LogStreamEnded, 'log-stream-ended')

    def LoadJsonFile(self) -> None:
        ''' Loads the .json configuration file. '''

        home = os.path.expanduser('~')

        if not os.path.isfile(f'{home}/.streamlink_looper.json'):
            proc = subprocess.run('streamlink --version', stdout=subprocess.PIPE, text=True)
            streamlink_version = proc.stdout.split()[1]

            self.appData['app_version'] = self.version
            self.appData['streamlink_version'] = streamlink_version
            self.appData['download_dir'] = f"{home}/Videos/Streamlink Looper"
            self.appData['wait_time'] = 15
            self.appData['log_verbosity'] = 'All'
            self.appData['clear_log'] = 1000
            self.appData['starts_scheduler_on_open'] = False
            self.appData['starts_with_computer'] = False
            self.appData['send_notifications'] = False

            self.appData['streamers_data'] = []

            with open(f'{home}/.streamlink_looper.json', 'w') as f:
                json.dump(self.appData, f, indent=4)

        else:
            with open(f'{home}/.streamlink_looper.json', 'r', encoding='utf-8') as f:
                text = f.read()
                self.appData = json.loads(text)

        if not os.path.isdir(self.appData['download_dir']):
            os.makedirs(self.appData['download_dir'])

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

        master.Add(self.scrolled, proportion=1, flag=wx.ALL | wx.EXPAND, border=5)
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

        start = self.scheduler_menu.Append(-1, 'Start', 'Start the scheduler.')
        pause = self.scheduler_menu.Append(-1, 'Pause', 'Pause the scheduler. The ongoing downloads remains active.')
        stop = self.scheduler_menu.Append(-1, 'Stop', 'Stop the scheduler and all ongoing downloads.')
        
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

    def GetStreamerPanel(self, streamer: str) -> wx.Panel:
        ''' Returns a Horizontal Sizer about a specific streamer. '''

        streamer_name = streamer['name']

        panel = wx.Panel(self.scrolled, name=streamer_name)
        panel.SetBackgroundColour('#ddd3ed')
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        textSize = (100, 23)
        name_t = wx.StaticText(panel, -1, streamer_name, size=textSize, style=wx.ALIGN_LEFT, name=streamer_name)
        clock = wx.StaticText(panel, -1, '00:00:00', size=textSize, style=wx.ALIGN_RIGHT, name=streamer_name)
        file_size = wx.StaticText(panel, -1, '0 B', size=textSize, style=wx.ALIGN_RIGHT, name=streamer_name)
        speed = wx.StaticText(panel, -1, '0 B/s', size=textSize, style=wx.ALIGN_RIGHT, name=streamer_name)

        sizer.Add(name_t, flag=wx.ALL, border=3)
        sizer.Add(clock, flag=wx.ALL, border=3)
        sizer.Add(file_size, flag=wx.ALL, border=3)
        sizer.Add(speed, flag=wx.ALL, border=3)

        panel.SetSizer(sizer)
        return panel

    def AddStreamer(self, streamer: dict):
        
        panel = self.GetStreamerPanel(streamer)

        self.scrolledSizer.Add(panel, flag=wx.ALL | wx.EXPAND, border=10)
        self.scrolled.SendSizeEvent()

    def Log(self, streamer: str, time: str, status: bool):
        ''' Adds to the log on the main window. '''

        self.rt.WriteText("The streamer ") 
        self.WriteStreamerName(streamer)
        self.rt.WriteText(f" was checked at {time} and it was ")
        self.WriteStreamerStatus(status)
        self.rt.WriteText(".\n")
        self.rt.MoveToLineEnd()

    def LogStreamEnded(self, streamer: str, time: str):
        ''' Adds to the log notifying about the ended stream. '''

        self.rt.WriteText("The ") 
        self.WriteStreamerName(streamer)
        self.rt.WriteText(f" stream ended at {time}")
        self.rt.WriteText(".\n")
        self.rt.MoveToLineEnd()

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

    def OnSettings(self, event) -> None:
        ''' Opens the settings window. '''

        frame = settings.Settings(self, self.appData)
        frame.ShowModal()

    def OnStart(self, event):
        ''' Starts the scheduler. '''

        if self.scheduler_status != 'Running':
            self.scheduler_thread = Scheduler(self, self.appData)
            self.scheduler_status = 'Running'
            self.scheduler_menu.Enable(self.ID.SCHEDULER, True)

    def OnTimer(self, event):
        ''' Called every second. '''

        pub.sendMessage('ping-timer')

    def UpdateDownloadInfo(self, name: str, watch: str, size: float, speed: float):
        ''' Updates a wx.Panel with a download info on `self.scrolled`. '''

        children = self.scrolled.GetChildren()
        for panel in children:
            if panel.GetName() == name:
                static_text_list = panel.GetChildren()
                static_text_list[1].SetLabel(watch)
                static_text_list[2].SetLabel(size)
                static_text_list[3].SetLabel(speed)

                return

    def DeletePanel(self, name: str):
        ''' Deletes a wx.Panel from the scrolledPanel. '''

        children = self.scrolled.GetChildren()
        for panel in children:
            if panel.GetName() == name:
                panel.Destroy()
                self.scrolled.SendSizeEvent()
                return
