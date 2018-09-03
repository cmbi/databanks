import os
import shutil

from databanks.pdb import pdb_path, pdb_flat_path
from databanks.settings import settings
from databanks.queue import Job
from databanks.command import log_command

import logging
_log = logging.getLogger(__name__)

script = "/usr/local/bin/mkbdb"
ccp4_setup = "/srv/data/bin/ccp4-7.0/bin/ccp4.setup-sh"

bdb_dir = os.path.join(settings["DATADIR"], "bdb")

def bdb_path(pdbid):
    return os.path.join(bdb_dir, pdbid[1:3], pdbid)

def bdb_obsolete(pdbid):
    out_path = os.path.join(bdb_path(pdbid), '%s.bdb' % pdbid)
    in_path = pdb_path(pdbid)
    return os.path.isfile(out_path) and (not os.path.isfile(in_path) or \
            os.path.getmtime(out_path) < os.path.getmtime(in_path))

def bdb_remove(pdbid):
    path = bdb_path(pdbid)
    if os.path.isdir(path):
        shutil.rmtree(path)

def bdb_uptodate(pdbid):
    in_path = pdb_path(pdbid)
    dir_path = bdb_path(pdbid)
    file_path = os.path.join(dir_path, "%s.bdb" % pdbid)
    whynot_path = os.path.join(dir_path, "%s.whynot" % pdbid)
    for path in [file_path, whynot_path]:
        if os.path.isfile(path) and (not os.path.isfile(in_path) or \
                os.path.getmtime(path) >= os.path.getmtime(in_path)):
            return True
    return False

class BdbJob(Job):
    def __init__(self, pdbid, pdb_extract_job=None):
        deps = []
        if pdb_extract_job is not None:
            deps.append(pdb_extract_job)
        Job.__init__(self, "bdb_%s" % pdbid, deps)
        self._pdbid = pdbid

    def run(self):
        log_command(_log, 'bdb',
                    ". %s; %s %s %s %s" % (
                        ccp4_setup, script,
                        bdb_dir,
                        pdb_flat_path(self._pdbid),
                        self._pdbid
                    )
        )

class BdbCleanupJob(Job):
    def __init__(self, pdb_fetch_job=None):
        dependent_jobs = []
        if pdb_fetch_job is not None:
            dependent_jobs.append(pdb_fetch_job)
        Job.__init__(self, "bdb_clean", dependent_jobs)

    def run(self):
        for part in os.listdir(bdb_dir):
            if len(part) == 2:
                for pdbid in os.listdir(os.path.join(bdb_dir, part)):
                    if bdb_obsolete(pdbid):
                        _log.warn("[bdb] removing %s" % pdbid)
                        bdb_remove(pdbid)
