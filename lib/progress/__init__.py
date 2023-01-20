from datetime import datetime
import sys
import asyncio
from functools import wraps, partial


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
