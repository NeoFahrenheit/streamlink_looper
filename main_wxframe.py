import os
import wx
import wx.richtext as rt
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
        self.status_bar = self.CreateStatusBar()

        self.shouldScrollDown = True
        self.version = 0.1
        self.appData = {}
        self.scheduler = []

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer)
        self.timer.Start(1000)

        self.LoadJsonFile()
        self.InitUI()
        self.CenterOnScreen()

        self.scheduler_thread = Scheduler(self, self.appData)
        pub.subscribe(self.UpdateDownloadInfo, 'update-download-info')
        pub.subscribe(self.DeleteRow, 'delete-panel')
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

        self.listCtrl = wx.ListCtrl(self.panel, -1, style=wx.LC_REPORT | wx.LC_HRULES)
        self.listCtrl.InsertColumn(0, 'Name', wx.LIST_FORMAT_CENTRE)
        self.listCtrl.InsertColumn(1, 'Time', wx.LIST_FORMAT_CENTRE)
        self.listCtrl.InsertColumn(2, 'Quality', wx.LIST_FORMAT_CENTRE)
        self.listCtrl.InsertColumn(3, 'Size', wx.LIST_FORMAT_CENTRE)
        self.listCtrl.InsertColumn(4, 'Speed', wx.LIST_FORMAT_CENTRE)

        self.listCtrl.SetColumnWidth(0, 150)
        self.listCtrl.SetColumnWidth(1, 80)
        self.listCtrl.SetColumnWidth(2, 80)
        self.listCtrl.SetColumnWidth(3, 80)
        self.listCtrl.SetColumnWidth(4, 80)

        self.rt = rt.RichTextCtrl(self.panel, -1, style=wx.TE_READONLY)
        self.rt.GetCaret().Hide()

        master.Add(self.listCtrl, proportion=1, flag=wx.ALL | wx.EXPAND, border=5)
        master.Add(self.rt, proportion=1, flag=wx.ALL | wx.EXPAND, border=5)

        self.panel.SetSizerAndFit(master)

    def InitMenu(self):
        menu = wx.MenuBar()

        file = wx.Menu()
        self.scheduler_menu = wx.Menu()
        log = wx.Menu()

        self.checkSubmenu = wx.Menu()
        self.stop_download = wx.Menu()

        settings = file.Append(-1, 'Settings', 'Open settings menu.')
        file.AppendSeparator()
        exit = file.Append(-1, 'Exit', 'Exit the software')

        start = self.scheduler_menu.Append(-1, 'Start', 'Start the scheduler.')
        pause = self.scheduler_menu.Append(-1, 'Pause', 'Pause the scheduler. The ongoing downloads remains active.')
        stop = self.scheduler_menu.Append(-1, 'Stop', 'Stop the scheduler and all ongoing downloads.')

        wait_time = wx.Menu()
        wait_time.Append(-1, 'and put back in the queue')
        wait_time.Append(-1, "and don't check for 8 hours")
        wait_time.Append(-1, "and don't check for 16 hours")
        wait_time.Append(-1, "and don't check for 24 hours")

        users = [name['name'] for name in self.appData['streamers_data']]
        for name in users:
            self.checkSubmenu.Append(-1, name, helpString=f"Check if {name} is online now.")
            self.stop_download.Append(-1, name, subMenu=wait_time)

        self.scheduler_menu.Append(self.ID.SCHEDULER, 'Check now...', self.checkSubmenu)
        self.scheduler_menu.Append(self.ID.SCHEDULER, 'Stop download from...', self.stop_download)
        #self.scheduler_menu.Enable(self.ID.SCHEDULER, False)
        
        log.Append(-1, 'Keep scrolled down', 'Keep the log scrolled down with every new message.', kind=wx.ITEM_CHECK)
        ver_choices = wx.Menu()
        ver_choices.Append(-1, 'All')
        ver_choices.Append(-1, 'Only streams going online')
        ver_choices.Append(-1, 'Only error messages')
        log.Append(-1, 'Verbosity', subMenu=ver_choices)

        self.Bind(wx.EVT_MENU, self.OnSettings, settings)
        self.Bind(wx.EVT_MENU, self.OnStart, start)
        self.Bind(wx.EVT_MENU, self.OnPause, pause)
        self.Bind(wx.EVT_MENU, self.OnStop, stop)

        menu.Append(file, 'File')
        menu.Append(self.scheduler_menu, 'Scheduler')
        menu.Append(log, 'Log')

        self.SetMenuBar(menu)

    def AddStreamer(self, streamer: dict):
        
        self.listCtrl.Append([streamer['name'], '00:00:00', '1080p60', '0 B', '0 B/s'])

    def Log(self, streamer: str, time: str, status: bool):
        ''' Adds to the log on the main window. '''

        self.rt.WriteText("The streamer ") 
        self.WriteStreamerName(streamer)
        self.rt.WriteText(f" was checked at {time} and it was ")
        self.WriteStreamerStatus(status)
        self.rt.WriteText(".\n")

        if self.shouldScrollDown:
            self.rt.ShowPosition(self.rt.GetLastPosition())

    def LogStreamEnded(self, streamer: str, time: str):
        ''' Adds to the log notifying about the ended stream. '''

        self.rt.WriteText("The ") 
        self.WriteStreamerName(streamer)
        self.rt.WriteText(f" stream ended at {time}")
        self.rt.WriteText(".\n")

        if self.shouldScrollDown:
            self.rt.ShowPosition(self.rt.GetLastPosition())

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

        if not self.scheduler_thread.isActive:
            self.scheduler_thread.isActive = True
            self.scheduler_thread.ChooseOne()
            
            self.scheduler_menu.Enable(self.ID.SCHEDULER, True)

    def OnPause(self, event):
        ''' Stops the scheduler (the thread remains active). The ongoing downloads remains active. '''

        self.scheduler_thread.isActive = False

    def OnStop(self, event):
        ''' Stop the scheduler (the thread remains active) and all ongoing downloads. '''

        if self.scheduler_thread.isActive:
            pub.sendMessage('kill-download-threads')
            self.scheduler_thread.isActive = False

    def OnTimer(self, event):
        ''' Called every second. '''

        pub.sendMessage('ping-timer')

    def UpdateDownloadInfo(self, name: str, watch: str | None, size: float | None, speed: float | None):
        ''' Updates a wx.Panel with a download info on `self.scrolled`. '''

        for i in range (0, self.listCtrl.GetItemCount()):
            if self.listCtrl.GetItemText(i, 0) == name:
                if watch:
                    self.listCtrl.SetItem(i, 1, watch)
                if size:
                    self.listCtrl.SetItem(i, 3, size)
                if speed:
                    self.listCtrl.SetItem(i, 4, speed)
                    
                return

    def DeleteRow(self, name: str):
        ''' Deletes a row in the wx.ListCtrl. '''

        for i in range (0, self.listCtrl.GetItemCount()):
            if self.listCtrl.GetItemText(i, 0) == name:
                self.listCtrl.DeleteItem(i)
                return
