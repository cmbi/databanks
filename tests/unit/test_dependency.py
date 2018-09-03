from nose.tools import ok_

from databanks.queue import Job, Queue


def test_dependency():

    # Job 2 depends on job 1,
    # so job 1 must run first.

    global ran1
    ran1 = False

    global ran2
    ran2 = False

    class Job1(Job):
        def run(self):
            global ran1
            ran1 = True

    class Job2(Job):
        def run(self):
            ok_(ran1)

            global ran2
            ran2 = True

    j1 = Job1('job1')
    j2 = Job2('job2', [j1])

    q = Queue(1)

    q.put(j2)
    q.put(j1)

    q.run()

    ok_(ran2)
