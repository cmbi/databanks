import os
import commands
from gzip import GzipFile
from subprocess import Popen, PIPE

from databanks.mmcif import mmcif_path
from databanks.dssp import dssp_path
from databanks.queue import Job
from databanks.settings import settings

import logging
_log = logging.getLogger(__name__)

MKPDBFINDER = "/srv/data/prog/pdbfinder/mkpdbfinder"
pdbfinder_dir = os.path.join(settings["DATADIR"], "pdbfinder/")


def dat_path(pdbid):
    return os.path.join(pdbfinder_dir, 'data/%s.dat' % pdbid)

def pdbfinder_uptodate(pdbid):
    in_path = mmcif_path(pdbid)
    out_path = dat_path(pdbid)
    return os.path.isfile(out_path) and \
            os.path.getmtime(out_path) >= os.path.getmtime(in_path) and \
            os.path.getmtime(out_path) >= os.path.getmtime(MKPDBFINDER)

def pdbfinder_obsolete(pdbid):
    out_path = dat_path(pdbid)
    in_path = mmcif_path(pdbid)
    return os.path.isfile(out_path) and not os.path.isfile(in_path)

def pdbfinder_remove(pdbid):
    path = dat_path(pdbid)
    if os.path.isfile(path):
        os.remove(path)

class PdbfinderDatJob(Job):
    def __init__(self, pdbid, dssp_job=None, hssp_job=None):
        dependent_jobs = []
        if dssp_job is not None:
            dependent_jobs.append(dssp_job)
        if hssp_job is not None:
            dependent_jobs.append(hssp_job)
        Job.__init__(self, "pdbfinder_%s" % pdbid, dependent_jobs)
        self._pdbid = pdbid

    def run(self):
        out_path = dat_path(self._pdbid)
        with open(out_path, 'w') as f:
            p = Popen([MKPDBFINDER, '-H'],
                      stdout=f, stderr=PIPE, stdin=PIPE,
                      cwd="/srv/data/prog/pdbfinder")
            p.stdin.write(self._pdbid)
            p.stdin.close()
            p.wait()
            for line in p.stderr:
                _log.error("[pdbfinder] %s" % line.strip())


class PdbfinderJoinJob(Job):
    def __init__(self, dat_jobs=[]):
        Job.__init__(self, "pdbfinder_join", dat_jobs)

    def run(self):
        dat_dir = os.path.join(pdbfinder_dir, "data/")
        out_file = os.path.join(pdbfinder_dir, "PDBFIND.TXT")
        gz_file = os.path.join(pdbfinder_dir, "PDBFIND.TXT.gz")

        _log.debug("[pdbfinder] generating %s" % out_file)
        with open(out_file, 'w') as f:
            p = Popen([MKPDBFINDER, '-A', dat_dir],
                      stdout=f, stderr=PIPE,
                      cwd="/srv/data/prog/pdbfinder")
            p.wait()
            for line in p.stderr:
                _log.error("[pdbfinder] %s" % line.strip())

        _log.debug("[pdbfinder] compressing %s" % out_file)
        with GzipFile(gz_file, 'wb') as g:
            with open(out_file, 'r') as f:
                while True:
                    chunk = f.read(1024)
                    if len(chunk) <= 0:
                        break
                    g.write(chunk)

class PdbfinderCleanupJob(Job):
    def __init__(self, mmcif_fetch_job):
        Job.__init__(self, "pdbfinder_clean", [mmcif_fetch_job])

    def run(self):
        for datname in os.listdir(os.path.join(settings["DATADIR"], "pdbfinder/data")):
            pdbid = datname[:4]
            if pdbfinder_obsolete(pdbid):
                _log.warn("[pdbfinder] removing %s" % pdbid)
                pdbfinder_remove(pdbid)
