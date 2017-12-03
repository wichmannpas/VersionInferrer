from datetime import datetime
import sys


class colors:
    RED = 1
    GREEN = 2
    YELLOW = 3
    BLUE = 4
    PURPLE = 5


def print_info(color, action, message):
    timestr = datetime.now().strftime('%H:%M:%S')
    print('[{timestr}] \x1b[3{color};1m{action}\x1b[0m: {message}'.format(
        timestr=timestr, color=color, action=action, message=message),
        file=sys.stderr)
