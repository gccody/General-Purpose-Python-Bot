import sys


class Progress:
    def __init__(self, msg: str, total: int):
        self.msg = msg
        self.iteration = 0
        self.total = total
        sys.stdout.write(f"\r{self.msg} [{self.iteration}/{self.total}]")
        sys.stdout.flush()

    def next(self):
        self.iteration += 1
        sys.stdout.write(f"\r{self.msg} [{self.iteration}/{self.total}]")
        sys.stdout.flush()
        if self.iteration == self.total:
            print("")
