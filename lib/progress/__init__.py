import asyncio
import sys
from datetime import datetime

from tqdm.asyncio import tqdm


def format_str(amount: int, string: str):
    if amount == 1:
        return string
    return string + 's'


def humanize(time):
    times = []
    times_to_ms = {
        'Year': 3154e7,
        'Month': 2628e6,
        'Week': 604800,
        'Day': 86400,
        'Hour': 3600,
        'Minute': 60,
        'Second': 1
    }
    for i, mod in times_to_ms.items():
        amount, time = divmod(time, mod)
        if amount == 0: continue
        times.append(f'{int(amount)} {format_str(amount, i)}')

    return ' '.join(times)


class Timer:
    start_time = datetime.now()

    async def start(self):
        print("\n")
        while True:
            await asyncio.sleep(1)
            sys.stdout.write(f"\r{humanize((datetime.now() - self.start_time).seconds)}")
            sys.stdout.flush()


class Progress:
    def __init__(self, msg: str, total: int):
        self.msg = msg
        self.iteration = 0
        self.total = total

    def start(self):
        sys.stdout.write(f"\r{self.msg} [{self.iteration}/{self.total}]")
        sys.stdout.flush()

    def next(self):
        if not self.total:
            print(self.msg)
        self.iteration += 1
        if self.iteration > self.total: raise ValueError("Can't iterate more then the total")
        sys.stdout.write(f"\r{self.msg} [{self.iteration}/{self.total}]")
        sys.stdout.flush()
        if self.iteration == self.total:
            print("")


class Loading:
    def __init__(self, msg: str):
        self.msg = msg
        self.iter = 0
        self.running = True
        self.length = 0

    async def start(self):
        while self.running:
            dots = ((self.iter % 3) + 1)
            string = f"\r{self.msg}{'.' * dots}{' '*(3-dots)}"
            self.length = len(string)
            sys.stdout.write(string)
            sys.stdout.flush()
            self.iter += 1
            await asyncio.sleep(0.5)
            if self.iter == 3:
                self.iter = 0

    def stop(self, finish_msg: str):
        self.running = False
        sys.stdout.write(f"\r{finish_msg}{' '*(self.length-len(finish_msg)) if len(finish_msg) <= self.length else ''}")
        sys.stdout.flush()
        print("")

