import os
import wx
import wx.richtext as rt
import wx.adv
import subprocess
from pubsub import pub
import json
from notifypy import Notify
from scheduler import Scheduler
import settings
import about
from enums import ID

class MainFrame(wx.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.STREAMER_COLOR = '#a970ff'
        self.STATUS_ON_COLOR = '#46734d'
        self.STATUS_OFF_COLOR = '#cc3535'

        self.SetTitle('Streamlink Lopper')
        self.SetSize(1000, 400)
        self.SetIcon(wx.Icon('media/icon_24.png'))
        self.status_bar = self.CreateStatusBar()

        self.verion = 0.1
        self.shouldScrollDown = True
        self.version = 0.1
        self.appData = {}
        self.scheduler = []
        
        self.home_path = os.path.expanduser('~')
        self.default_download_path = f"{self.home_path}\\Videos\\Streamlink Looper"
        self.Bind(wx.EVT_ICONIZE, self.OnClose)

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer)
        self.timer.Start(1000)

        self.LoadJsonFile()
        self.InitUI()
        self.CenterOnScreen()

        self.taskBarIcon = TaskBarIcon(self)

        self.scheduler_thread = Scheduler(self, self.appData)
        if self.appData['start_on_scheduler']:
            self.OnStart(None)

        self.menu.Check(ID.MENU_LOG_CHECKBOX, self.appData['log_scroll_down'])
        
        pub.subscribe(self.UpdateDownloadInfo, 'update-download-info')
        pub.subscribe(self.DeleteRow, 'delete-panel')
        pub.subscribe(self.SaveFile, 'save-file')
        pub.subscribe(self.Log, 'log')
        pub.subscribe(self.LogStreamEnded, 'log-stream-ended')

        self.Bind(wx.EVT_ICONIZE, self.OnMinimize)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        self.taskBarIcon.CreatePopupMenu()

    def LoadJsonFile(self) -> None:
        ''' Loads the .json configuration file. '''

        if not os.path.isfile(f'{self.home_path}/.streamlink_looper.json'):
            proc = subprocess.run('streamlink --version', stdout=subprocess.PIPE, text=True)
            streamlink_version = proc.stdout.split()[1]

            self.appData['app_version'] = self.version
            self.appData['streamlink_version'] = streamlink_version
            self.appData['download_dir'] = self.default_download_path
            self.appData['wait_time'] = 30
            self.appData['start_on_scheduler'] = False
            self.appData['tray_on_minimized'] = False
            self.appData['tray_on_closed'] = False
            self.appData['send_notifications'] = True
            self.appData['log_scroll_down'] = True
            self.appData['ID_count'] = 2000

            self.appData['streamers_data'] = []

            with open(f'{self.home_path}/.streamlink_looper.json', 'w') as f:
                json.dump(self.appData, f, indent=4)

        else:
            with open(f'{self.home_path}/.streamlink_looper.json', 'r', encoding='utf-8') as f:
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

        self.listCtrl = wx.ListCtrl(self.panel, -1, style=wx.LC_REPORT)
        self.listCtrl.Bind(wx.EVT_LIST_INSERT_ITEM, self.OnListCtrlModified)
        self.listCtrl.Bind(wx.EVT_LIST_DELETE_ITEM, self.OnListCtrlModified)

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

        self.notification = Notify(
        default_notification_title = "Someone is online.",
        default_notification_application_name = "Streamlink Looper",
        default_notification_icon = 'media/icon_64.png',
        default_notification_audio = 'media/notification_sound.wav'
        )

        self.panel.SetSizerAndFit(master)

    def InitMenu(self):
        self.menu = wx.MenuBar()

        file = wx.Menu()
        self.scheduler_menu = wx.Menu()
        log = wx.Menu()
        help = wx.Menu()

        self.checkSubmenu = wx.Menu()
        self.stop_download = wx.Menu()

        settings = file.Append(-1, 'Settings', 'Open settings menu.')
        file.AppendSeparator()
        self.exit = file.Append(-1, 'Exit', 'Exit the software')

        start = self.scheduler_menu.Append(-1, 'Start', 'Start the scheduler.')
        pause = self.scheduler_menu.Append(-1, 'Pause', 'Pause the scheduler. The ongoing downloads remains active.')
        stop = self.scheduler_menu.Append(-1, 'Stop', 'Stop the scheduler and all ongoing downloads.')

        wait_time = wx.Menu()
        wait_time.Append(ID.PUT_BACK, 'and put back in the queue')
        wait_time.Append(ID.WAIT_8, "and don't check for 8 hours")
        wait_time.Append(ID.WAIT_16, "and don't check for 16 hours")
        wait_time.Append(ID.WAIT_24, "and don't check for 24 hours")

        users = [name['name'] for name in self.appData['streamers_data']]
        for name in users:
            check = self.checkSubmenu.Append(ID.MENU_CHECK, name, helpString=f"Check if {name} is online now.", )
            self.Bind(wx.EVT_MENU, self.OnMenuCheckNow, check)

            stop = self.stop_download.Append(ID.MENU_STOP, name, subMenu=wait_time)
            self.Bind(wx.EVT_MENU, self.OnMenuStopNow, stop)

        self.scheduler_menu.Append(ID.SCHEDULER, 'Check now...', self.checkSubmenu)
        self.scheduler_menu.Append(ID.SCHEDULER, 'Stop download from...', self.stop_download)
        #self.scheduler_menu.Enable(ID.SCHEDULER, False)
        
        self.log_scroll = log.Append(ID.MENU_LOG_CHECKBOX, 'Keep scrolled down', 'Keep the log scrolled down with every new message.', kind=wx.ITEM_CHECK)
        log_clear = log.Append(-1, 'Clear log', 'Clear all the text in the log.')

        about = help.Append(-1, "About Streamlink Looper")

        self.Bind(wx.EVT_MENU, self.OnSettings, settings)
        self.Bind(wx.EVT_MENU, self.OnStart, start)
        self.Bind(wx.EVT_MENU, self.OnPause, pause)
        self.Bind(wx.EVT_MENU, self.OnStop, stop)

        self.Bind(wx.EVT_MENU, self.OnLogScroll, self.log_scroll)
        self.Bind(wx.EVT_MENU, self.OnLogClear, log_clear)

        self.Bind(wx.EVT_MENU, self.OnAbout, about)

        self.Bind(wx.EVT_MENU, self.OnExit, self.exit)

        self.menu.Append(file, 'File')
        self.menu.Append(self.scheduler_menu, 'Scheduler')
        self.menu.Append(log, 'Log')
        self.menu.Append(help, 'Help')

        self.SetMenuBar(self.menu)

    def AddStreamer(self, streamer: dict):
        
        self.listCtrl.Append([streamer['name'], '00:00:00', '1080p60', '0 B', '0 B/s'])
        if self.appData['send_notifications']:
            self.notification.message = f"The streamer {streamer['name']} is online!"
            self.notification.send(block=False)

    def Log(self, streamer: str, time: str, status: bool):
        ''' Adds to the log on the main window. '''

        self.rt.WriteText("The streamer ") 
        self.WriteStreamerName(streamer)
        self.rt.WriteText(f" was checked at {time} and it was ")
        self.WriteStreamerStatus(status)
        self.rt.WriteText(".\n")

        if self.appData['log_scroll_down']:
            self.rt.ShowPosition(self.rt.GetLastPosition())

    def LogStreamEnded(self, streamer: str, time: str):
        ''' Adds to the log notifying about the ended stream. '''

        self.rt.WriteText("The ") 
        self.WriteStreamerName(streamer)
        self.rt.WriteText(f" stream ended at {time}")
        self.rt.WriteText(".\n")

        if self.appData['log_scroll_down']:
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
            
            self.scheduler_menu.Enable(ID.SCHEDULER, True)

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

    def UpdateDownloadInfo(self, name: str, watch: str, quality: str, size: float, speed: float):
        ''' Updates a wx.Panel with a download info on `self.scrolled`. '''

        for i in range (0, self.listCtrl.GetItemCount()):
            if self.listCtrl.GetItemText(i, 0) == name:
                if watch:
                    self.listCtrl.SetItem(i, 1, watch)
                if quality:
                    self.listCtrl.SetItem(i, 2, quality)
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

    def OnListCtrlModified(self, event):
        """ Called when an item is inserted or deleted from the wx.ListCtrl. """

        lenght = self.listCtrl.GetItemCount()
        for i in range(0, lenght):
            if i % 2 == 0:
                self.listCtrl.SetItemBackgroundColour(i, '#f1e6ff')
            else:
                self.listCtrl.SetItemBackgroundColour(i, wx.NullColour)

    def OnLogScroll(self, event):
        """ Called when the user click on the log scroll menu. """

        obj = event.GetEventObject()
        value = obj.IsChecked(ID.MENU_LOG_CHECKBOX)
        self.appData['log_scroll_down'] = value
        pub.sendMessage('save-file')

    def OnLogClear(self, event):
        """ Called when the user click on the clear log menu. """

        self.rt.Clear()

    def OnMenuCheckNow(self, event):

        name = event.GetEventObject().GetLabel(ID.MENU_CHECK)
        print(f'{name} ta online?')
    
    def OnMenuStopNow(self, event):

        name = event.GetEventObject().GetLabel(ID.MENU_STOP)

        print('Fulana, para!')

    def OnAbout(self, event):
        """ Called when the user clicks on Help -> About. """

        frame = about.About(self)
        frame.ShowModal()

    def OnShowFrame(self, event):
        # Restore Frame if it is minimized.
        if self.IsIconized():
            self.Restore()

        # Show MainFrame if it is not shown already.
        if self.IsShown():
            # Frame is already visible. Flash it.
            self.RequestUserAttention()
            self.SetFocus()

        else:
            self.Show()

    def OnMinimize(self, event):
        """ Called when the windows is minimized. """

        if self.appData['tray_on_minimized'] and self.IsIconized():
            self.Hide()

    def OnRightClickTaskbar(self, event):
        """ Called when the TaskBar icon is right clicked. """

        ...

    def OnClose(self, event):
        """ Called when the user tries to close the window. """

        if self.appData['tray_on_closed'] and self.taskBarIcon.IsAvailable():
            self.Hide()

        else:
            self.taskBarIcon.Destroy()
            self.Destroy()

    def OnExit(self, event):
        """ Truly exits the program, no matter what settings is on. """

        self.taskBarIcon.Destroy()
        self.Destroy()



class TaskBarIcon(wx.adv.TaskBarIcon):
    def __init__(self, parent):
        wx.adv.TaskBarIcon.__init__(self)
        
        self.parent = parent
        self.SetIcon(wx.Icon('media/icon_24.png'), 'Streamlink Looper')

        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, parent.OnShowFrame)

    def CreatePopupMenu(self):
        return self.parent.scheduler_menu