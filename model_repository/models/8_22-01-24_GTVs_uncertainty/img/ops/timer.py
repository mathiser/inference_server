from timeit import default_timer as timer
from datetime import timedelta

class TimeOP:
    def __init__(self, name):
        self.name = name
        self.start = timer()

    def report(self):
        t = timer()
        return f"{self.name} finished. Took: {timedelta(seconds=t-self.start)}"
