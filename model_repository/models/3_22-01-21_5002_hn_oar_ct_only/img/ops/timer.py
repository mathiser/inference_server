import logging
from timeit import default_timer as timer
from datetime import timedelta

class TimeOP:
    def __init__(self, name, logger):
        self.logger = logger
        self.name = name
        self.start = timer()

def end_and_report(self):
    self.logger.info(f"{self.name} finished. Took: {timedelta(seconds=timer()-self.start)}")
