import sys
import os
from signal import SIGTERM
from threading import Lock, Thread
from time import sleep

root_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(root_path)

from databanks.data import SchedulePdbDataJob, ScheduleMmcifDataJob, SchedulePdbredoDataJob

class _FakeQueue:
    def __init__(self):
        self._print_lock = Lock()

    def put(self, job, priority=0):
        with self._print_lock:
            print job.get_name()

class _RunThread(Thread):
    def __init__(self, schedule_job):
        Thread.__init__(self)
        self._schedule_job = schedule_job

    def run(self):
        self._schedule_job.run()

queue = _FakeQueue()

threads = []
for schedule_job in [ScheduleMmcifDataJob(queue, None, None, None),
                     SchedulePdbDataJob(queue, None),
                     SchedulePdbredoDataJob(queue, None)]:
    t = _RunThread(schedule_job)
    t.start()
    threads.append(t)

try:
    # (for some reason, t.join ignores KeyboardInterrupt here)
    while any([t.is_alive() for t in threads]):
        sleep(1)
except (KeyboardInterrupt, SystemExit):
    # Make this process terminate itself, since threads don't recieve KeyboardInterrupt
    os.kill(os.getpid(), SIGTERM)
