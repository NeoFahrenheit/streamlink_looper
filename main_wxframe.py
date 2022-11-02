from hashlib import new
import os
import wx
import wx.richtext as rt
import wx.adv
import subprocess
from pubsub import pub
import json
from datetime import datetime, timedelta
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
        self.SetSize(1000, 600)
        self.SetIcon(wx.Icon('media/icon_24.png'))
        self.status_bar = self.CreateStatusBar()

        self.verion = 0.1
        self.version = 0.1
        self.appData = {}

        self.home_path = os.path.expanduser('~')
        self.default_download_path = f"{self.home_path}/Videos/Streamlink Looper"
        self.nameOnPopup = ''
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
        pub.subscribe(self.UpdateWaitUntilOnFile, 'update-wait-until')
        pub.subscribe(self.DeleteRow, 'delete-panel')
        pub.subscribe(self.SaveFile, 'save-file')
        pub.subscribe(self.Log, 'log')
        pub.subscribe(self.LogStreamEnded, 'log-stream-ended')

        pub.subscribe(self.AddToTree, 'add-to-tree')
        pub.subscribe(self.EditInTree, 'edit-in-tree')
        pub.subscribe(self.RemoveFromTree, 'remove-from-tree')

        self.Bind(wx.EVT_ICONIZE, self.OnMinimize)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def LoadJsonFile(self) -> None:
        ''' Loads the .json configuration file. '''

        if not os.path.isfile(f'{self.home_path}/.streamlink_looper.json'):
            proc = subprocess.run(['streamlink', '--version'], stdout=subprocess.PIPE, text=True)
            streamlink_version = proc.stdout.split()[1]

            self.appData['app_version'] = self.version
            self.appData['streamlink_version'] = streamlink_version
            self.appData['download_dir'] = self.default_download_path
            self.appData['start_on_scheduler'] = False
            self.appData['tray_on_minimized'] = False
            self.appData['tray_on_closed'] = False
            self.appData['send_notifications'] = False
            self.appData['log_scroll_down'] = True

            self.appData['domains'] = {}
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
        masterSizer = wx.BoxSizer(wx.VERTICAL)
        upperSizer = wx.BoxSizer(wx.HORIZONTAL)

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

        self.tree = wx.TreeCtrl(self.panel, -1)
        self.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.OnTreeRightClick, self.tree)

        self.tree_root = self.tree.AddRoot('Streamers')
        self.tree_downloading = self.tree.AppendItem(self.tree_root, 'Being downloaded')
        self.tree_queue = self.tree.AppendItem(self.tree_root, 'On the queue')
        self.tree_fridge = self.tree.AppendItem(self.tree_root, 'On the fridge')

        self.AppendsItemsOnTreeAtStart()
        self.tree.ExpandAll()

        upperSizer.Add(self.listCtrl, proportion=1, flag=wx.ALL | wx.EXPAND, border=5)
        upperSizer.Add(self.tree, proportion=1, flag=wx.ALL | wx.EXPAND, border=5)

        masterSizer.Add(upperSizer, proportion=2, flag=wx.ALL | wx.EXPAND, border=5)
        masterSizer.Add(self.rt, proportion=1, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM| wx.EXPAND, border=10)

        self.notification = Notify(
        default_notification_title = "Someone is online.",
        default_notification_application_name = "Streamlink Looper",
        default_notification_icon = 'media/icon_64.png',
        default_notification_audio = 'media/notification_sound.wav'
        )

        self.panel.SetSizerAndFit(masterSizer)

    def InitMenu(self):
        self.menu = wx.MenuBar()

        file = wx.Menu()
        scheduler_menu = wx.Menu()
        log = wx.Menu()
        help = wx.Menu()

        self.checkSubmenu = wx.Menu()
        self.stop_download = wx.Menu()

        settings = file.Append(-1, 'Settings', 'Open settings menu.')
        file.AppendSeparator()
        self.exit = file.Append(-1, 'Exit', 'Exit the software')

        start = scheduler_menu.Append(-1, 'Start', 'Start the scheduler.')
        pause = scheduler_menu.Append(-1, 'Pause', 'Pause the scheduler. The ongoing downloads remains active.')
        stop = scheduler_menu.Append(-1, 'Stop', 'Stop the scheduler and all ongoing downloads.')
        
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
        self.menu.Append(scheduler_menu, 'Scheduler')
        self.menu.Append(log, 'Log')
        self.menu.Append(help, 'Help')

        self.SetMenuBar(self.menu)

    def AppendsItemsOnTreeAtStart(self):
        """ Appends items on the Tree on app start. """

        isAppDataChanged = False

        for i in range (0, len(self.appData['streamers_data'])):
            name = self.appData['streamers_data'][i]['name']

            if self.appData['streamers_data'][i]['wait_until']:
                now = datetime.now()
                until = datetime.strptime(self.appData['streamers_data'][i]['wait_until'], "%Y-%m-%d %H:%M:%S")

                if now < until:
                    self.tree.AppendItem(self.tree_fridge, name)
                else:
                    self.appData['streamers_data'][i]['wait_until'] = ''
                    isAppDataChanged = True

            else:
                self.tree.AppendItem(self.tree_queue, name)

        if isAppDataChanged:
            self.SaveFile()

    def AddStreamer(self, streamer: dict):
        """ Adds the streamer to the wx.ListCtrl. """
        
        self.listCtrl.Append([streamer['name'], '00:00:00', '1080p60', '0 B', '0 B/s'])
        self.AddToTree(streamer['name'], ID.TREE_DOWNLOADING)

        if self.appData['send_notifications']:
            self.notification.message = f"The {streamer['name']}'s stream is online!"
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
            self.scheduler_thread.start()

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
                break

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

    def OnTreeRightClick(self, event):
        """ Called when an item on the tree is right clicked. Pops a context menu. """

        item = event.GetItem()
        clickedOn = self.tree.GetItemText(item)

        parent = self.tree.GetItemParent(item)
        if parent:
            parent_text = self.tree.GetItemText(parent)
        else:
            return

        self.nameOnPopup = clickedOn
        self.parent_tree = parent_text

        menu = wx.Menu()
        match parent_text:
            case 'Being downloaded':
                put_back = menu.Append(ID.PUT_BACK, f"Stop and put back in the queue")
                wait_8 = menu.Append(ID.WAIT_8, f"Stop and don't check for 8 hours")
                wait_16 = menu.Append(ID.WAIT_16, f"Stop and don't check for 16 hours")
                wait_24 = menu.Append(ID.WAIT_24, f"Stop and don't check for 24 hours")

                self.Bind(wx.EVT_MENU, self.OnPopupMenu, put_back)
                self.Bind(wx.EVT_MENU, self.OnPopupMenu, wait_8)
                self.Bind(wx.EVT_MENU, self.OnPopupMenu, wait_16)
                self.Bind(wx.EVT_MENU, self.OnPopupMenu, wait_24)

            case 'On the queue':
                check_now = menu.Append(ID.CHECK_NOW, f"Check now")
                wait_8 = menu.Append(ID.WAIT_8, f"Don't check for 8 hours")
                wait_16 = menu.Append(ID.WAIT_16, f"Don't check for 16 hours")
                wait_24 = menu.Append(ID.WAIT_24, f"Don't check for 24 hours")

                self.Bind(wx.EVT_MENU, self.OnPopupMenu, check_now)
                self.Bind(wx.EVT_MENU, self.OnPopupMenu, wait_8)
                self.Bind(wx.EVT_MENU, self.OnPopupMenu, wait_16)
                self.Bind(wx.EVT_MENU, self.OnPopupMenu, wait_24)

            case 'On the fridge':
                remove = menu.Append(ID.REMOVE_FROM_FRIDGE, f"Remove from fridge")
                remove_and_check = menu.Append(ID.REMOVE_FROM_FRIDGE_CHECK, f"Remove from fridge and check now")

                self.Bind(wx.EVT_MENU, self.OnPopupMenu, remove)
                self.Bind(wx.EVT_MENU, self.OnPopupMenu, remove_and_check)

            case _:
                return

        scr = wx.GetMousePosition()
        rel = self.ScreenToClient(scr)
        self.PopupMenu(menu, rel)

    def AddToTree(self, name: str, parent_id):
        """ Add a node to the Tree. """

        match parent_id:
            case ID.TREE_DOWNLOADING:
                self.tree.AppendItem(self.tree_downloading, name)

            case ID.TREE_QUEUE:
                self.tree.AppendItem(self.tree_queue, name)

            case ID.TREE_FRIDGE:
                self.tree.AppendItem(self.tree_fridge, name)

        self.tree.Refresh()

    def EditInTree(self, oldName: str, newName: str):
        """ Edit a node in the Tree. """

        if oldName == newName:
            return

        item = self.GetItemByName(oldName, self.tree_root)
        if item.IsOk():
            self.tree.SetItemText(item, newName)

        self.tree.Refresh()

    def RemoveFromTree(self, name: str, parent_id):
        """ Removes a node from the tree by name. """

        match parent_id:
            case ID.TREE_DOWNLOADING:
                parent_node = self.tree_downloading

            case ID.TREE_QUEUE:
                parent_node = self.tree_queue

            case ID.TREE_FRIDGE:
                parent_node = self.tree_fridge

            case ID.TREE_ALL:
                parent_node = self.tree_root

        item = self.GetItemByName(name, parent_node)
        if item.IsOk():
            self.tree.Delete(item)
            self.tree.Refresh()

    def GetItemByName(self, name, root_item):
        item, cookie = self.tree.GetFirstChild(root_item)

        while item.IsOk():
            text = self.tree.GetItemText(item)
            if text.lower() == name.lower():
                return item
            if self.tree.ItemHasChildren(item):
                match = self.GetItemByName(name, item)
                if match.IsOk():
                    return match
            item, cookie = self.tree.GetNextChild(root_item, cookie)

        return wx.TreeItemId()

    def UpdateWaitUntilOnFile(self, name: str, date_time: str = None):
        """ Updates a streamer's ['wait_until'] key on file. """

        for i in range(0, len(self.appData['streamers_data'])):
            if self.appData['streamers_data'][i]['name'] == name:
                if date_time:
                    self.appData['streamers_data'][i]['wait_until'] = date_time
                else:
                    self.appData['streamers_data'][i]['wait_until'] = ''
                
                self.SaveFile()
                return

    def OnPopupMenu(self, event):
        """ Called when the user clicks on something on the PopupMenu. """

        id = event.GetId()

        match self.parent_tree:

            case 'Being downloaded':
                if id == ID.PUT_BACK:
                    self.scheduler_thread.RemoveFromThread(self.nameOnPopup)
                    self.RemoveFromTree(self.nameOnPopup, ID.TREE_DOWNLOADING)
                    self.tree.AppendItem(self.tree_queue, self.nameOnPopup)

                elif id == ID.WAIT_8:
                    self.tree.AppendItem(self.tree_fridge, self.nameOnPopup)
                    self.ProcessFridgeTime(id)

                elif id == ID.WAIT_16:
                    self.tree.AppendItem(self.tree_fridge, self.nameOnPopup)
                    self.ProcessFridgeTime(id)

                elif id == ID.WAIT_24:
                    self.tree.AppendItem(self.tree_fridge, self.nameOnPopup)
                    self.ProcessFridgeTime(id)
                    

            case 'On the queue':
                if id == ID.CHECK_NOW:
                    streamer = self.scheduler_thread.GetStreamerByName(self.nameOnPopup)
                    self._CheckStreamerNow(streamer)

                else:
                    self.RemoveFromTree(self.nameOnPopup, ID.TREE_QUEUE)
                    self.tree.AppendItem(self.tree_fridge, self.nameOnPopup)
                    self.ProcessFridgeTime(id)

            case 'On the fridge':
                
                self.RemoveFromTree(self.nameOnPopup, ID.TREE_FRIDGE)
                self.tree.AppendItem(self.tree_queue, self.nameOnPopup)

                if id == ID.REMOVE_FROM_FRIDGE:
                    self.scheduler_thread.TransferFromFridgeToQueue(self.nameOnPopup)

                elif id == ID.REMOVE_FROM_FRIDGE_CHECK:
                    self.scheduler_thread.TransferFromFridgeToQueue(self.nameOnPopup)
                    streamer = self.scheduler_thread.GetStreamerByName(self.nameOnPopup)
                    self._CheckStreamerNow(streamer)
                    

    def _CheckStreamerNow(self, streamer: dict):
        """ Check if's a streamer is online now. Meant to be called only in the MainFrame. 
        It does everything else. """

        now = datetime.now()
        status = self.scheduler_thread.CheckStreamer(streamer)
        name = streamer['name']

        if status:
            self.AddStreamer(streamer)

            self.scheduler_thread.RemoveFromQueue(name)
            self.RemoveFromTree(name, parent_id=ID.TREE_QUEUE)  
            self.RemoveFromTree(name, parent_id=ID.TREE_FRIDGE)

        time = now.strftime("%H:%M:%S")
        self.Log(name, time, status)

    def ProcessFridgeTime(self, id: ID):
        """ Process the time a streamer will be on the fridge. It also removes the
        streamer from the scheduler thread and saves the file. """

        self.scheduler_thread.RemoveFromThread(self.nameOnPopup)
        self.RemoveFromTree(self.nameOnPopup, ID.TREE_DOWNLOADING)

        wait = 0
        match id:
            case ID.WAIT_8:
                wait = 8
            case ID.WAIT_16:
                wait = 16
            case ID.WAIT_24:
                wait = 24

        until = datetime.now() + timedelta(hours=wait)
        until_str = datetime.strftime(until, "%Y-%m-%d %H:%M:%S")
        self.UpdateWaitUntilOnFile(self.nameOnPopup, until_str)

class TaskBarIcon(wx.adv.TaskBarIcon):
    def __init__(self, parent):
        wx.adv.TaskBarIcon.__init__(self)
        
        self.parent = parent
        self.SetIcon(wx.Icon('media/icon_24.png'), 'Streamlink Looper')

        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, parent.OnShowFrame)

    # def CreatePopupMenu(self):
    #     return self.parent.scheduler_menu