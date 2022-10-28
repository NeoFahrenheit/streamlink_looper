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
        tree_donwloading = self.tree.AppendItem(self.root, 'Being downloaded')
        tree_queue = self.tree.AppendItem(self.root, 'On the queue')
        tree_fridge = self.tree.AppendItem(self.root, 'On the fridge')

        for s in streamers:
            self.tree.AppendItem(tree_donwloading, s)

        self.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.OnTree, self.tree)
        self.tree.ExpandAll()

    def OnTree(self, event):
        item = event.GetItem()
        parent = self.tree.GetItemParent(item)
        if parent:
            parent_text = self.tree.GetItemText(parent)
        else:
            parent_text = 'root'

        print(f'Double clicked on {self.tree.GetItemText(item)}, under {parent_text}')

        menu = wx.Menu()
        menu.Append( -1, 'aaaaaaaaa' )

        ### 5. Launcher displays menu with call to PopupMenu, invoked on the source component, passing event's GetPoint. ###
        self.PopupMenu( menu, event.GetPoint() )

app = wx.App()
frame = Frame(None).Show()
app.MainLoop()


# import wx

# class TreeExample(wx.Frame):
#     def __init__(self):
#         wx.Frame.__init__(self, None, title='Tree Example', size=(200, 130))
#         self.tree = wx.TreeCtrl(self, size=(200, 100))

#         root = self.tree.AddRoot('root')
#         for item in ['item1', 'item2', 'item3']:
#             self.tree.AppendItem(root, item)
#         self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.OnActivated, self.tree)
#         self.tree.Expand(root)

#     def OnActivated(self, evt):
#         print(f'Double clicked on {self.tree.GetItemText(evt.GetItem())}')

# app = wx.PySimpleApp(None)
# TreeExample().Show()
# app.MainLoop()