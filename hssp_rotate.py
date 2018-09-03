#!/usr/bin/python

import os
import sys
from sets import Set
from bz2 import BZ2File

from databanks.settings import settings
from databanks.queue import Queue, Job
from databanks.hssp import HsspJob, HgHsspJob

import logging
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
_log = logging.getLogger(__name__)


def count_hits(stockholm_path):
    hits = Set()
    with BZ2File(stockholm_path) as f:
        for line in f:
            if line.startswith('#=GS'):
                id_ = line.split()[1]
                hits.add(id_)
    return len(hits)


class HsspScheduleJob(Job):
    def __init__(self, queue):
        Job.__init__(self, "hssp_schedule", [])
        self._queue = queue

    def run(self):
        hssp3_dir = os.path.join(settings['DATADIR'], 'hssp3')
        hssp3_paths = [os.path.join(hssp3_dir, filename)
                          for filename in os.listdir(hssp3_dir)]

        hghssp_dir = os.path.join(settings['DATADIR'], 'hg-hssp')
        hghssp_paths = [os.path.join(hghssp_dir, filename)
                            for filename in os.listdir(hghssp_dir)]

        # Oldest files go first:
        for path in sorted(hssp3_paths + hghssp_paths,
                           key=os.path.getmtime):

            # Not the ones with 9999 hits:
            try:
                if count_hits(path) >= 9999:
                    if path.startswith(hssp3_dir):
                        pdbid = os.path.basename(path).split('.')[0]
                        self._queue.put(HsspJob(pdbid))
                    elif path.startswith(hghssp_dir):
                        seq_id = os.path.basename(path).split('.')[0]
                        self._queue.put(HgHsspJob(seq_id))
            except:
                continue


if __name__ == "__main__":
    q = Queue(12)
    q.put(HsspScheduleJob(q))
    q.run()
