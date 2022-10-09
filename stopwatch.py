'''
A simple stopwatch. It will be pinged every second by
the wx.Timer in the main thread. Since, this is more performant than a standart
time.time() implementation.
'''

class StopWatch():
    def __init__(self):
        self.sec = 0
        self.min = 0
        self.hour = 0

    def ping(self):
        ''' Increments this stopwatch by one second. '''

        self.sec += 1
        if self.sec > 59:
            self.sec = 0
            self.min += 1

        if self.min > 59:
            self.min = 0
            self.hour += 1

    def to_str(self) -> str:
        return f"{self.hour:02}:{self.min:02}:{self.sec:02}"

    def __str__(self) -> str:
        return f"{self.hour:02}:{self.min:02}:{self.sec:02}"