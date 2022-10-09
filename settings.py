from tkinter import HORIZONTAL
import wx

class Settings(wx.Dialog):
    def __init__(self, parent, appData: list):
        super().__init__(parent)

        self.SetTitle('Settings')
        self.appData = appData

        self.InitUI()
        self.LoadData()

        self.CenterOnParent()

    def InitUI(self) -> None:
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.notebook = wx.Notebook(self, -1)
        sizer.Add(self.notebook, flag=wx.ALL | wx.EXPAND, border=5)

        streamers = self.GetStreamersPanel()

        self.notebook.AddPage(streamers, 'Streamers')

        self.SetSizerAndFit(sizer)

    def LoadData(self) -> None:
        ''' Load the data for the streamers. '''

        streamers = self.appData['streamers_data']
        for streamer in streamers:
            self.listBox.Append(streamer['name'])

    def GetStreamersPanel(self) -> wx.Panel:
        panel = wx.Panel(self.notebook)
        masterSizer = wx.BoxSizer(wx.HORIZONTAL)
        listSizer = wx.BoxSizer(wx.VERTICAL)
        detailsSizer = wx.BoxSizer(wx.VERTICAL)

        masterSizer.Add(listSizer, flag=wx.ALL, border=10)
        masterSizer.Add(detailsSizer, flag=wx.ALL | wx.EXPAND, border=10)

        textSize = (100, 23)
        addBtn = wx.Button(panel, -1, 'Add')
        removeBtn = wx.Button(panel, -1, 'Remove')
        self.listBox = wx.ListBox(panel, -1, size=(150, 150))
        self.ListBox.Bind(wx.EVT_LISTBOX, self.OnListBox)

        urlSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.urlCtrl = wx.TextCtrl(panel, -1, size=(200, 23))
        urlSizer.Add(wx.StaticText(panel, -1, ' Streamer URL :', size=textSize, style=wx.ALIGN_RIGHT), flag=wx.TOP, border=3)
        urlSizer.Add(self.urlCtrl, flag=wx.LEFT, border=15)

        nameSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.nameCtrl = wx.TextCtrl(panel, -1, size=(200, 23))
        nameSizer.Add(wx.StaticText(panel, -1, ' Streamer name :', size=textSize, style=wx.ALIGN_RIGHT), flag=wx.TOP, border=3)
        nameSizer.Add(self.nameCtrl, flag=wx.LEFT, border=15)

        prioritySizer = wx.BoxSizer(wx.HORIZONTAL)
        self.priorityCtrl = wx.SpinCtrl(panel, -1, size=(50, 23), min=1)
        prioritySizer.Add(wx.StaticText(panel, -1, 'Priority :', size=textSize, style=wx.ALIGN_RIGHT), flag=wx.TOP, border=3)
        prioritySizer.Add(self.priorityCtrl, flag=wx.LEFT, border=15)

        qualitySizer = wx.BoxSizer(wx.HORIZONTAL)
        choices = ['best', '1080p', '720p', '480p', '360p', '240p', '144p']
        self.qualityCombo = wx.ComboBox(panel, -1, choices[0], choices=choices, size=(100, 23), style=wx.CB_READONLY)
        qualitySizer.Add(wx.StaticText(panel, -1, 'Quality :', size=textSize, style=wx.ALIGN_RIGHT), flag=wx.TOP, border=3)
        qualitySizer.Add(self.qualityCombo, flag=wx.LEFT, border=15)

        detailsSizer.Add(urlSizer)
        detailsSizer.Add(nameSizer, flag=wx.TOP, border=10)
        detailsSizer.Add(prioritySizer, flag=wx.TOP, border=10)
        detailsSizer.Add(qualitySizer, flag=wx.TOP, border=10)

        buttonsSizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonsSizer.Add(addBtn)
        buttonsSizer.Add(removeBtn, flag=wx.LEFT, border=10)

        listSizer.Add(buttonsSizer, flag=wx.BOTTOM, border=10)
        listSizer.Add(self.listBox, flag=wx.EXPAND)

        panel.SetSizer(masterSizer)
        return panel


    def OnListBox(self, event) -> None:
        ''' Call every time the users clicks on something in the wx.ListBox. '''

        print(event.GetID())