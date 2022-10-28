import os
import wx
import wx.richtext as rt
from pubsub import pub
import platform
import webbrowser
import streamlink
from enums import ID

class Settings(wx.Dialog):
    def __init__(self, parent, appData: list):
        super().__init__(parent)

        self.SetTitle('Settings')
        self.appData = appData

        self.InitUI()
        self.LoadData()

        self.CenterOnParent()

        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def InitUI(self) -> None:
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.notebook = wx.Notebook(self, -1)
        sizer.Add(self.notebook, flag=wx.ALL | wx.EXPAND, border=5)

        streamers = self.GetStreamersPanel()
        preferences = self.GetPreferencesPanel()

        self.notebook.AddPage(streamers, 'Streamers')
        self.notebook.AddPage(preferences, 'Preferences')

        self.SetSizerAndFit(sizer)

    def LoadData(self) -> None:
        ''' Load the data for the streamers and the controls. '''

        streamers = self.appData['streamers_data']
        if streamers:
            for streamer in streamers:
                self.listBox.Append(streamer['name'])

            self.listBox.SetSelection(0)
            self.OnListBox(None)
        
        self.waitCtrl.SetValue(self.appData['wait_time'])
        self.startCheckBox.SetValue(self.appData['start_on_scheduler'])
        self.trayMinimizeCheckBox.SetValue(self.appData['tray_on_minimized'])
        self.trayCloseCheckBox.SetValue(self.appData['tray_on_closed'])
        self.notificationCheckBox.SetValue(self.appData['send_notifications'])
        self.dirCtrl.SetValue(self.appData['download_dir'])

    def GetStreamersPanel(self) -> wx.Panel:
        ''' Gets the streamer panel. '''

        panel = wx.Panel(self.notebook)
        masterSizer = wx.BoxSizer(wx.HORIZONTAL)
        listSizer = wx.BoxSizer(wx.VERTICAL)
        detailsSizer = wx.BoxSizer(wx.VERTICAL)

        masterSizer.Add(listSizer, flag=wx.ALL, border=10)
        masterSizer.Add(detailsSizer, flag=wx.ALL, border=10)

        textSize = (75, 23)
        removeBtn = wx.Button(panel, -1, 'Remove')
        createBtn = wx.Button(panel, -1, 'Create')
        editBtn = wx.Button(panel, -1, 'Edit')
        clearBtn = wx.Button(panel, -1, 'Clear')

        clearBtn.Bind(wx.EVT_BUTTON, self.OnClear)
        removeBtn.Bind(wx.EVT_BUTTON, self.OnRemove)
        createBtn.Bind(wx.EVT_BUTTON, self.OnCreate)
        editBtn.Bind(wx.EVT_BUTTON, self.OnEdit)

        self.listBox = wx.ListBox(panel, -1)
        self.listBox.Bind(wx.EVT_LISTBOX, self.OnListBox)

        urlSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.urlCtrl = wx.TextCtrl(panel, -1, size=(250, 23))
        urlSizer.Add(wx.StaticText(panel, -1, 'URL :', size=textSize, style=wx.ALIGN_RIGHT), flag=wx.TOP, border=3)
        urlSizer.Add(self.urlCtrl, flag=wx.LEFT, border=15)

        nameSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.nameCtrl = wx.TextCtrl(panel, -1, size=(250, 23))
        nameSizer.Add(wx.StaticText(panel, -1, 'Name :', size=textSize, style=wx.ALIGN_RIGHT), flag=wx.TOP, border=3)
        nameSizer.Add(self.nameCtrl, flag=wx.LEFT, border=15)

        prioritySizer = wx.BoxSizer(wx.HORIZONTAL)
        self.priorityCtrl = wx.SpinCtrl(panel, -1, size=(50, 23), min=1, max=5)
        prioritySizer.Add(wx.StaticText(panel, -1, 'Priority :', size=textSize, style=wx.ALIGN_RIGHT), flag=wx.TOP, border=3)
        prioritySizer.Add(self.priorityCtrl, flag=wx.LEFT, border=15)

        qualitySizer = wx.BoxSizer(wx.HORIZONTAL)
        choices = ['best', 'high', 'medium', 'low', 'worst', 'audio only']
        self.qualityCombo = wx.ComboBox(panel, -1, choices[0], choices=choices, size=(100, 23), style=wx.CB_READONLY)
        qualitySizer.Add(wx.StaticText(panel, -1, 'Quality :', size=textSize, style=wx.ALIGN_RIGHT), flag=wx.TOP, border=3)
        qualitySizer.Add(self.qualityCombo, flag=wx.LEFT, border=15)

        detailsSizer.Add(urlSizer)
        detailsSizer.Add(nameSizer, flag=wx.TOP, border=10)
        detailsSizer.Add(prioritySizer, flag=wx.TOP, border=10)
        detailsSizer.Add(qualitySizer, flag=wx.TOP, border=10)

        BtnSizer = wx.BoxSizer(wx.HORIZONTAL)
        BtnSizer.Add(editBtn, flag=wx.ALIGN_CENTER)
        BtnSizer.Add(createBtn, flag=wx.LEFT | wx.ALIGN_CENTER, border=50)
        detailsSizer.Add(BtnSizer, flag=wx.TOP | wx.ALIGN_CENTER, border=50)

        buttonsSizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonsSizer.Add(clearBtn)
        buttonsSizer.Add(removeBtn, flag=wx.LEFT, border=10)

        listSizer.Add(buttonsSizer, proportion=1, flag=wx.BOTTOM, border=10)
        listSizer.Add(self.listBox, proportion=5, flag=wx.EXPAND)

        panel.SetSizer(masterSizer)
        return panel

    def GetPreferencesPanel(self) -> wx.Panel:
        ''' Gets the preferences panel. '''

        panel = wx.Panel(self.notebook)
        sizer = wx.BoxSizer(wx.VERTICAL)
        textSize = (100, 23)
        longTextSize = (285, 23)

        waitSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.waitCtrl = wx.SpinCtrl(panel, -1, size=(60, 23), min=5, max=120, initial=15)
        waitSizer.Add(wx.StaticText(panel, -1, 'Wait time :', size=((60, 23))), flag=wx.TOP, border=3)
        waitSizer.Add(self.waitCtrl, flag=wx.LEFT, border=15)

        startSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.startCheckBox = wx.CheckBox(panel, -1)
        startSizer.Add(self.startCheckBox, flag=wx.RIGHT, border=10)
        startSizer.Add(wx.StaticText(panel, -1, 'Starts the scheduler when the app is opened', size=longTextSize))
        self.Bind(wx.EVT_CHECKBOX, self.OnStartCheckBox, self.startCheckBox)

        trayMinimizeSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.trayMinimizeCheckBox = wx.CheckBox(panel, -1)
        trayMinimizeSizer.Add(self.trayMinimizeCheckBox, flag=wx.RIGHT, border=10)
        trayMinimizeSizer.Add(wx.StaticText(panel, -1, 'Go to system tray when minimized.', size=longTextSize))
        self.Bind(wx.EVT_CHECKBOX, self.OnMinimizeTrayCheckBox, self.trayMinimizeCheckBox)

        trayCloseSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.trayCloseCheckBox = wx.CheckBox(panel, -1)
        trayCloseSizer.Add(self.trayCloseCheckBox, flag=wx.RIGHT, border=10)
        trayCloseSizer.Add(wx.StaticText(panel, -1, 'Go to system tray when closed.', size=longTextSize))
        self.Bind(wx.EVT_CHECKBOX, self.OnCloseTrayCheckBox, self.trayCloseCheckBox)

        notificationSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.notificationCheckBox = wx.CheckBox(panel, -1)
        notificationSizer.Add(self.notificationCheckBox, flag=wx.RIGHT, border=10)
        notificationSizer.Add(wx.StaticText(panel, -1, 'Send notifications about streamers going online', size=longTextSize))
        self.Bind(wx.EVT_CHECKBOX, self.OnNotificationCheckBox, self.notificationCheckBox)

        dirSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.dirCtrl = wx.TextCtrl(panel, -1, '', size=(300, 23))
        dirBtn = wx.Button(panel, -1, 'Choose')
        dirBtn.Bind(wx.EVT_BUTTON, self.OnChooseDir)
        dirSizer.Add(wx.StaticText(panel, -1, 'Download folder :', size=textSize, style=wx.ALIGN_RIGHT), flag=wx.TOP, border=3)
        dirSizer.Add(self.dirCtrl, flag=wx.LEFT, border=15)
        dirSizer.Add(dirBtn, flag=wx.LEFT, border=15)

        sizer.Add(waitSizer, flag=wx.TOP | wx.LEFT, border=10)
        sizer.Add(startSizer, flag=wx.TOP | wx.LEFT, border=10)
        sizer.Add(trayMinimizeSizer, flag=wx.TOP | wx.LEFT, border=10)
        sizer.Add(trayCloseSizer, flag=wx.TOP | wx.LEFT, border=10)
        sizer.Add(notificationSizer, flag=wx.TOP | wx.LEFT, border=10)
        sizer.Add(dirSizer, flag=wx.TOP, border=10)

        panel.SetSizer(sizer)
        return panel

    def GetFieldsData(self) -> dict:
        ''' Returns the data on the fields through a dictionary. '''

        data = {}
        url = self.urlCtrl.GetValue().strip()
        name = self.nameCtrl.GetValue().strip()
        priority = self.priorityCtrl.GetValue()
        quality = self.qualityCombo.GetValue()
        
        data['url'] = url
        data['name'] = name
        data['quality'] = quality
        data['priority'] = priority

        return data


    def OnListBox(self, event) -> None:
        ''' Call every time the users clicks on something in the wx.ListBox. '''

        if not event:
            index = 0
        else:
            index = event.GetEventObject().GetSelection()
        
        if self.appData['streamers_data']:
            data = self.appData['streamers_data'][index]
            self.urlCtrl.SetValue(data['url'])
            self.nameCtrl.SetValue(data['name'])
            self.priorityCtrl.SetValue(data['priority'])
            self.qualityCombo.SetValue(data['quality'])

        else:
            self.OnClear(None)

    def OnClear(self, event):
        ''' Reset the field to their default values. '''

        self.urlCtrl.Clear()
        self.nameCtrl.Clear()
        self.priorityCtrl.SetValue(1)
        self.qualityCombo.SetValue('best')

        self.listBox.SetSelection(wx.NOT_FOUND)

    def OnRemove(self, event):
        ''' Removes a streamer from the file. '''

        index = self.listBox.GetSelection()
        if index == wx.NOT_FOUND:
            dlg = wx.MessageDialog(self, f"Please, select a streamer to remove.", 'No streamer selected', wx.ICON_ERROR)
            return

        name = self.appData['streamers_data'][index]['name']
        dlg = wx.MessageDialog(self, f"Are you sure you want to remove {name}? If there is a livestream from it being downloaded, it will be canceled.",
         'Removing streamer', wx.ICON_WARNING | wx.YES_NO)
        res = dlg.ShowModal()

        if res == wx.ID_YES:
            self.listBox.Delete(index)
            del self.appData['streamers_data'][index]
            pub.sendMessage('save-file')
            pub.sendMessage('remove-from-thread', name=name)
            pub.sendMessage('remove-from-queue', name=name)
            wx.CallAfter(pub.sendMessage, topicName='remove-from-tree', name=name, parent_id=ID.TREE_ALL)

            self.OnListBox(None)

    def OnCreate(self, event):
        if self.urlCtrl.IsEmpty() or self.nameCtrl.IsEmpty():
            wx.MessageBox('Please, fill all the information in the text fields.', 'Empty Fields', wx.ICON_ERROR)
            return

        data = self.GetFieldsData()

        for streamer in self.appData['streamers_data']:
            if streamer['name'] == data['name']:
                wx.MessageBox('A streamer with this name already exists. Please, choose another one.', 
                'Streamer already exists', wx.ICON_ERROR)
                return
        
        data['wait_until'] = ''
        self.appData['streamers_data'].append(data)
        pub.sendMessage('add-to-queue', streamer=data)
        wx.CallAfter(pub.sendMessage, topicName='add-to-tree', name=data['name'], parent_id=ID.TREE_QUEUE)

        pub.sendMessage('save-file')
        self.listBox.Append(data['name'])

        wx.MessageBox('Streamer successfully saved.', 'Success', wx.ICON_INFORMATION)

    def OnEdit(self, event):
        if self.urlCtrl.IsEmpty() or self.nameCtrl.IsEmpty():
            wx.MessageBox('Please, fill all the information in the text fields.', 'Empty Fields', wx.ICON_ERROR)
            return

        index = self.listBox.GetSelection()
        data = self.GetFieldsData()
        if index == wx.NOT_FOUND:
            wx.MessageBox('Please, select a streamer to edit.', 'No streamer selected', wx.ICON_ERROR)
            return

        oldName = self.listBox.GetString(index)
        # If the user is editing without changing the name, we need a exception for cheking
        # that. Hence, i != index.
        for i in range (0, len(self.appData['streamers_data'])):
            if i != index and self.appData['streamers_data'][i]['name'] == data['name']:
                wx.MessageBox('A streamer with this name already exists. Please, choose another one.', 
                'Streamer already exists', wx.ICON_ERROR)
                return

        self.EditStreamerOnFile(index, oldName, data)
        self.listBox.SetString(index, data['name'])
        pub.sendMessage('scheduler-edit', oldName=oldName, inData=data)

        wx.MessageBox(f"{data['name']} was successfully saved.", 'Success', wx.ICON_INFORMATION)

    def EditStreamerOnFile(self, index: int, oldName: str, inData: dict):
        ''' Edit the stream in the given index with inData. '''

        self.appData['streamers_data'][index]['url'] = inData['url']
        self.appData['streamers_data'][index]['name'] = inData['name']
        self.appData['streamers_data'][index]['quality'] = inData['quality']
        self.appData['streamers_data'][index]['priority'] = inData['priority']
        self.appData['streamers_data'][index]['wait_until'] = inData['wait_until']
        
        pub.sendMessage('save-file')
        pub.sendMessage('scheduler-edit', oldName=oldName, inData=inData)

    def OnChooseDir(self, event):
        """ Called when the user clicks the Choose Dir button. """

        path = os.path.expanduser('~')
        dialog = wx.DirDialog(self, 'Choose the download folder', f"{path}/Videos")
        if dialog.ShowModal() == wx.ID_OK:
            user_path = dialog.GetPath()
            self.dirCtrl.SetValue(user_path)
            self.appData['download_dir'] = user_path
            pub.sendMessage('save-file')

    def OnCloseTrayCheckBox(self, event):
        """ Called when user clicks on close to system tray checkbox. """

        obj = event.GetEventObject()
        value = obj.GetValue()
        self.appData['tray_on_closed'] = value
        pub.sendMessage('save-file')
    
    def OnMinimizeTrayCheckBox(self, event):
        """ Called when user clicks on minimize to system tray checkbox. """

        obj = event.GetEventObject()
        value = obj.GetValue()
        self.appData['tray_on_minimized'] = value
        pub.sendMessage('save-file')

    def OnStartCheckBox(self, event):
        """ Called when user clicks on start the scheduler when the app is opened checkbox. """

        obj = event.GetEventObject()
        value = obj.GetValue()
        self.appData['start_on_scheduler'] = value
        pub.sendMessage('save-file')

    def OnNotificationCheckBox(self, event):
        """ Called when user clicks on the notification checkbox. """

        obj = event.GetEventObject()
        value = obj.GetValue()
        self.appData['send_notifications'] = value
        pub.sendMessage('save-file')

    def OnClose(self, event):
        """ Called when the user tries to close the window. """

        self.Destroy()