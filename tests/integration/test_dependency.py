from nose.tools import ok_

from databanks.queue import Queue
from databanks.fetch import (FetchPdbJob, FetchMmcifJob, FetchUniprotJob)
from databanks.data import ScheduleMmcifDataJob


def test_mmcif_data_dependency():

    global uniprot_job
    uniprot_job = FetchUniprotJob()

    global mmcif_job
    mmcif_job = FetchMmcifJob()

    global pdb_job
    pdb_job = FetchPdbJob()

    class TestScheduleMmcifDataJob(ScheduleMmcifDataJob):
        def run(self):
            global uniprot_job
            ok_(uniprot_job.done)

            global mmcif_job
            ok_(mmcif_job.done)

            global pdb_job
            ok_(pdb_job.done)

            ScheduleMmcifDataJob.run(self)

    queue = Queue(32)

    data_job = TestScheduleMmcifDataJob(queue, mmcif_job, pdb_job, uniprot_job)

    queue.put(data_job)
    queue.put(uniprot_job)
    queue.put(mmcif_job)
    queue.put(pdb_job)

    queue.run()

    ok_(data_job.done)
