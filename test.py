import wx

class ID:
    WAIT_8 = 1001
    WAIT_16 = 1002
    WAIT_24 = 1003

    TREE_DOWNLOADING = 1004
    TREE_QUEUE = 1005
    TREE_FRIDGE = 1006

streamers = ['Geoge', 'Vanessa', 'Iris', 'Mark', 'Paul']

class Frame(wx.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.a = self.CreateStatusBar()

        self.tree = wx.TreeCtrl(self, -1)

        self.root = self.tree.AddRoot('Streamers')
        downloading_id = tree_donwloading = self.tree.AppendItem(self.root, 'Being downloaded')
        queue_id = tree_queue = self.tree.AppendItem(self.root, 'On the queue')
        fridge_id = tree_fridge = self.tree.AppendItem(self.root, 'On the fridge')

        for s in streamers:
            self.tree.AppendItem(tree_donwloading, s)

        self.tree.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.OnTree)

    def OnTree(self, event):
        sel = self.tree.GetSelection()

        print(sel)

app = wx.App()
frame = Frame(None).Show()
app.MainLoop()