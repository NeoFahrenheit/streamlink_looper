# Streamlink Looper

Have you gone to work or school and came back home only to find out that your favorite streamer lost the connection, restarted the livestream soon afterwards and you lost the entire recording because the script ended?

Now, you can add your favorite streamer to the software so you can never lose a livestream again.


## Features

 - Add your streamer to the catalog and set priorities to them.
   Streamers with higher priorities get checked for online avaialibility
   more often.
 - Set the time to wait before another stream is checked again. Therefore, you can control how much you stress the livestream servers and potencially avoid being IP blocked.
 - Powerful log system. See what the scheduler is doing in real time.
 - Powerful feedback system. See the low long a stream is being record, the current file size and download speed for each of them.

## Current bugs and problems

 - Reported download speed is inconsistent and it takes too long to update.

## TODO

 - Test livestreams from other websites (only Twitch is being tested right now).

## How to run the app

First, you need to make sure if you have all the dependencies installed.

 1. [wxPython](https://www.wxpython.org/pages/downloads/)
 2. [pypubsub](https://pypubsub.readthedocs.io/en/v4.0.3/installation.html)
 3. [streamlink](https://pypi.org/project/streamlink/)
 4. [notify.py](https://github.com/ms7m/notify-py)

All the other libraries should come with Python by default. At a later point, when the software becames more robust and stable, an *.exe* installer will be provided.

## Contributing

All contribution is welcomed. The software is in the start part of it's development and all help is apreciated.

![Image of the main window with some streams being downloaded.](https://i.imgur.com/sieJFNe.png)
