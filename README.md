# streamlink_looper
## A tiny Python script that runs your streamlink command on loop!

Have you gone to your work or school and came back home only to find out that your favorite stream lost the connection, restarted the livestream soon afterwards and you lost the entire recording because the script ended?

This python script is for you, then!
It only works for twitch.tv for now, but you can change to work with whatever plataform you like.

USAGE:
<br>
Open a Command Prompt / Terminal where the script is located and type:<br>
**python streamlink_looper.py "your command"**

EXAMPLE:
<br>
**python streamlink_looper.py "streamlink twitch.tv/streamer_name best --twitch-disable-hosting --retry-streams 60 -o streamer_name.mp4"**

REQUIREMENTS:
<br>
You need the streamlink installed and in your path.
<br>
You need to have python installed and in your path.
