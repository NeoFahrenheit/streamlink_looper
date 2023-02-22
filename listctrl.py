import wx
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin

class ListCtrl(wx.ListCtrl, ListCtrlAutoWidthMixin):
    def __init__(self, parent):
        wx.ListCtrl.__init__(self, parent, -1, style=wx.LC_REPORT)
        ListCtrlAutoWidthMixin.__init__(self)

        self.SetupColumns()

    def SetupColumns(self):
        ''' Create and configure the columns. '''

        self.InsertColumn(0, 'Name', wx.LIST_FORMAT_CENTRE)
        self.InsertColumn(1, 'Time', wx.LIST_FORMAT_CENTRE)
        self.InsertColumn(2, 'Quality', wx.LIST_FORMAT_CENTRE)
        self.InsertColumn(3, 'Size', wx.LIST_FORMAT_CENTRE)
        self.InsertColumn(4, 'Speed', wx.LIST_FORMAT_CENTRE)

        self.SetColumnWidth(0, 150)
        self.SetColumnWidth(1, 90)
        self.SetColumnWidth(2, 90)
        self.SetColumnWidth(3, 90)
        self.SetColumnWidth(4, 90)

        self.setResizeColumn(0)