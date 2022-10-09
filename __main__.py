from wx import App
import main_wxframe

if __name__ == "__main__":
    app = App()
    frame = main_wxframe.MainFrame(None)
    frame.Show()
    app.MainLoop()
