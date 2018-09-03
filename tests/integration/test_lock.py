from databanks.lock import FileLock
from threading import Thread
from time import sleep
from nose.tools import eq_

lock_path = "/tmp/test_lock"

class LockThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.done = False

    def run(self):
        with FileLock(lock_path) as f:
            self.done = True

def test_filelock():
    t = LockThread()
    with FileLock(lock_path) as f:
        t.start()
        sleep(5)

        eq_(t.done, False)

    t.join()
    eq_(t.done, True)
