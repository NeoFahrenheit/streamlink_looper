# Streamlink Looper

Have you gone to your work or school and came back home only to find out that your favorite stream lost the connection, restarted the livestream soon afterwards and you lost the entire recording because the script ended?

Now, you can add your favorite streams to the software so you can never lose a livestream from them again.


## Features

 - Add your streamers to the catalog and set priorities to them.
   Streamers with higher priorities get checked for online avaialibility
   more often.
 - Set the time to wait before another stream is checked again. Therefore, you can control how much you stress the livestream website and potencially avoid being IP blocked.
 - Powerful log system. See what the scheduler is doing in real time.
 - Powerful feedback system. See the low long a stream is being record, the current file size and download speed for each of them.

## Current bugs and problems

 - Reported download speed is inconsistent and it takes too long to update.
 - Sometimes when a stream is checked, the app lags a bit causing the timer for freeze for one or two seconds and causing problems with the formatting of text strings to the log.

## TODO

 - Different scheduler for each different livestream websites. Set different wait time for each of them. They must not conflict with each other.
 - Finish setting up the logic for the Preferences in the Settings window.
 - Add the feature to stop and pause the scheduler.
 - Add the feature to check if a specific streamer is online immediately.

## Rename a file

You can rename the current file by clicking the file name in the navigation bar or by clicking the **Rename** button in the file explorer.

## How to run the app

First, you need to make sure if you have all the dependencies installed.

 1. [wxPython](https://www.wxpython.org/pages/downloads/)
 2. [pypubsub](https://pypubsub.readthedocs.io/en/v4.0.3/installation.html)
 3. [m3u8](https://github.com/globocom/m3u8)
 4. [streamlink](https://pypi.org/project/streamlink/)
 5. [ffmpeg](https://ffmpeg.org/download.html) on PATH (Optional)

All the other libraries should come with Python by default. At a later point, when the software becames more robust, an *.exe* installer will be provided.

## Contributing

All contribution is welcomed. The software is in the start part of it's development and all help is apreciated.

![Image of the main window with some streams being downloaded.](https://i.imgur.com/NxzMso9.png)