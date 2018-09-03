from nose.tools import ok_

from databanks.queue import Queue, Job

class TestJob(Job):
    def __init__(self):
        Job.__init__(self, "test")
        self.test_done = False
    def run(self):
        self.test_done = True

class TestJobJob(Job):
    def __init__(self, queue):
	Job.__init__(self, "test_job")
	self.test_done = False
	self._queue = queue
    def run(self):
	self.job = TestJob()
	self._queue.put(self.job)
	self.test_done = True

def test_queue():
    q = Queue(2)

    jobs = []
    for i in range(4):
        job = TestJob()
        q.put(job)
        jobs.append(job)
    q.run()

    for job in jobs:
        ok_(job.test_done)

def test_queue_twice():
    q = Queue(2)

    for j in range(2):
        jobs = []
        for i in range(4):
            job = TestJob()
            q.put(job)
            jobs.append(job)
        q.run()

        for job in jobs:
            ok_(job.test_done)

def test_queue_flex():
    q = Queue(2)

    jobs = []
    for i in range(4):
        job = TestJobJob(q)
        q.put(job)
        jobs.append(job)
    q.run()

    for job in jobs:
        ok_(job.test_done)
	ok_(job.job.test_done)

def test_empty_queue():
    q = Queue(2)
    q.run()
