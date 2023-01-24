from datetime import datetime
import sys
import asyncio


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
        sys.stdout.write(f"\r{self.msg} {self.iteration/self.total*100:.2f}%")
        sys.stdout.flush()

    def next(self):
        if not self.total:
            print(self.msg)
        self.iteration += 1
        if self.iteration > self.total: raise ValueError("Can't iterate more then the total")
        sys.stdout.write(f"\r{self.msg} {self.iteration/self.total*100:.2f}%")
        sys.stdout.flush()
        if self.iteration == self.total:
            print("")


class Loading:
    def __init__(self, msg: str):
        self.msg = msg
        self.step = 0
        self.pause = .5
        self.done = False

    async def start(self):
        while not self.done:
            sys.stdout.write(f"\r{self.msg}{'.'*((self.step%3)+1)}")
            sys.stdout.flush()
            self.step += 1
            await asyncio.sleep(self.pause)
            if self.done:
                break
        print("")

    def stop(self):
        self.done = True
