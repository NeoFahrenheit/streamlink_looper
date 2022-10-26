import wx
import wx.richtext as rt
import platform
import webbrowser
import streamlink

class About(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent)

        self.parent = parent
        self.SetTitle('About')
        self.SetSize((350, 400))
        self.CenterOnParent()

        self.initUI()

        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

    def initUI(self):
        ''' Inicializa a UI. '''

        master = wx.BoxSizer(wx.VERTICAL)

        logo = wx.StaticBitmap(self, -1, wx.Bitmap('media/icon_64.png'))
        name = wx.StaticText(self, -1, 'Streamlink Looper\n')
        ver = wx.StaticText(self, -1, f'Version: {self.parent.version}')
        pyVer = wx.StaticText(self, -1, f'Python: {platform.python_version()}')
        wxVer = wx.StaticText(self, -1, f'wxPython: {wx.__version__}')
        streamlinkVer = wx.StaticText(self, -1, f'Streamlink: {streamlink.__version__}')
        self.rtc = rt.RichTextCtrl(self, -1, size=(300, 150), style=wx.TE_READONLY)
        self.rtc.GetCaret().Hide()
        self.rtc.Bind(wx.EVT_TEXT_URL, self.OnURL)

        self.writeInBold('Programmer:')
        self.rtc.Newline()
        self.writeInURL('https://www.linkedin.com/in/leandro-monteiro-037bbb75/', 'Leandro Monteiro')
        self.rtc.Newline()

        self.writeInBold('Dependencies:')
        self.rtc.Newline()
        self.writeInURL('https://github.com/streamlink/streamlink', 'Streamlink')
        self.writeInURL('https://www.wxpython.org/', 'wxPython')
        self.writeInURL('https://pypubsub.readthedocs.io/en/v4.0.3/index.html', 'pypubsub')
        self.writeInURL('https://github.com/ms7m/notify-py', 'notify.py')
        self.rtc.Newline()

        self.writeInBold('Contact:')
        self.rtc.Newline()
        self.writeInURL('https://github.com/NeoFahrenheit/streamlink_looper', 'GitHub')
        self.writeInURL('https://twitter.com/NeoFahrenheit', 'Twitter')
        self.writeBlueUnderlined('neofahrenheit@outlook.com')
        self.rtc.Newline()
        self.rtc.Newline()

        self.writeInBold('Media sources:')
        self.rtc.Newline()
        self.writeInURL('https://notificationsounds.com/message-tones/out-of-nowhere-message-tone', 'Notification sound')
        self.writeInURL('https://www.flaticon.com/br/icone-gratis/laco_6711752#', 'App logo', False)

        master.Add(logo, flag=wx.ALL | wx.ALIGN_CENTER, border=10)
        master.Add(name, flag=wx.LEFT | wx.RIGHT | wx.TOP | wx.ALIGN_CENTER, border=10)
        master.Add(ver, flag=wx.ALIGN_CENTER)
        master.Add(pyVer, flag=wx.ALIGN_CENTER)
        master.Add(wxVer, flag=wx.ALIGN_CENTER)
        master.Add(streamlinkVer, flag=wx.ALIGN_CENTER)
        master.Add(self.rtc, flag=wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER, border=15)

        self.SetSizer(master)

    def writeInBold(self, text):
        ''' Escreve `text` em self.rtc em negrito e depois muda para o estilo padrão. '''

        self.rtc.ApplyBoldToSelection()
        self.rtc.WriteText(text)
        self.rtc.SetDefaultStyle(wx.TextAttr())

    def writeInURL(self, url, text, appendNewLine=True):
        ''' Escreve `text` em self.rtc no estilo URL e depois muda para o estilo padrão. '''

        self.rtc.BeginTextColour(wx.BLUE)
        self.rtc.BeginUnderline()
        self.rtc.BeginURL(url)
        self.rtc.WriteText(text)
        if appendNewLine: self.rtc.AppendText('')

        self.rtc.EndTextColour()
        self.rtc.EndUnderline()
        self.rtc.EndURL()

    def OnURL(self, event):
        ''' Chamada quando algum link é clicado. Abre o link no browser padrão da máquina. '''

        webbrowser.open_new(event.GetString())

    def writeBlueUnderlined(self, text):
        ''' Escreve `text` em azul com sublinhado. '''

        self.rtc.BeginTextColour(wx.BLUE)
        self.rtc.BeginUnderline()

        self.rtc.WriteText(text)

        self.rtc.EndTextColour()
        self.rtc.EndUnderline()

    def OnCloseWindow(self, event):
        ''' Fecha a janela. '''

        self.parent.aboutWindow = None
        self.Destroy()