class ID():
    ''' Using as enums. '''
    
    def __init__(self):
        self.SCHEDULER = 1000


def get_unit(size: int) -> str:
    unit = ''
    if size < 1024:
        unit = 'B'
    elif size < 1_048_576:
        unit = 'KB'
    elif size < 1_073_741_824:
        unit = 'MB'
    else:
        unit = 'GB'

    return unit


def get_downloaded_value(size: int) -> float:
    if size < 1024:
        return size
    elif size < 1_048_576:
        return size / 1024
    elif size < 1_073_741_824:
        return size / 1_048_576
    else:
        return size / 1_073_741_824


def get_progress_text(stopwatch, dl_total: float, dl_temp: float) -> tuple:
    ''' Returns a tuple (stopwatch, downloaded, speed). '''

    downloaded = get_downloaded_value(dl_total)
    unit_downloaded = get_unit(dl_total)

    speed = get_downloaded_value(dl_temp)
    speed_unit = get_unit(dl_temp)

    t = (stopwatch.to_str(), f"{downloaded:.2f} {unit_downloaded}", f"{speed:.2f} {speed_unit}/s")
    return t