import os
from gzip import GzipFile

from databanks.queue import Job
from databanks.settings import settings
from databanks.command import log_command
from databanks.pdbfinder import dat_path as pdbfinder_path
from databanks.mmcif import mmcif_path

import logging
_log = logging.getLogger(__name__)

pdbfinder2_dir = os.path.join(settings["DATADIR"], "pdbfinder2/")
PDBFINDER2_SCRIPT = "/srv/data/prog/pdbfinder2/what_modelbase.py"

def dat_path(pdbid):
    return os.path.join(pdbfinder2_dir, 'data/%s.dat' % pdbid)

def pdbfinder2_uptodate(pdbid):
    in_path = mmcif_path(pdbid)
    out_path = dat_path(pdbid)
    return os.path.isfile(out_path) and \
            os.path.getmtime(out_path) >= os.path.getmtime(in_path) and \
            os.path.getmtime(out_path) >= os.path.getmtime(PDBFINDER2_SCRIPT)

def pdbfinder2_obsolete(pdbid):
    in_path = mmcif_path(pdbid)
    out_path = dat_path(pdbid)
    return os.path.isfile(out_path) and not os.path.isfile(in_path)

def pdbfinder2_remove(pdbid):
    path = dat_path(pdbid)
    if os.path.isfile(path):
        os.remove(path)

class Pdbfinder2DatJob(Job):
    def __init__(self, pdbid, pdbfinder_job=None):
        if pdbfinder_job is None:
            Job.__init__(self, "pdbfinder2_%s" % pdbid)
        else:
            Job.__init__(self, "pdbfinder2_%s" % pdbid, [pdbfinder_job])
        self._pdbid = pdbid

    def run(self):
        _log.info("[pdbfinder2] mkpdbfinder2 %s" % self._pdbid)

        log_command(_log, 'pdbfinder2',
            "python2 " + PDBFINDER2_SCRIPT + " -pdbftopdbf2" +
            " %s" % (self._pdbid.lower()),
            cwd="/srv/data/prog/pdbfinder2/"
        )

class Pdbfinder2JoinJob(Job):
    def __init__(self, dat_jobs=[]):
        Job.__init__(self, "pdbfinder2_join", dat_jobs)

    def run(self):
        dat_dir = os.path.join(pdbfinder2_dir, "data/")
        out_file = os.path.join(pdbfinder2_dir, "PDBFIND2.TXT")
        gz_file = os.path.join(pdbfinder2_dir, "PDBFIND2.TXT.gz")

        log_command(_log, 'pdbfinder2',
            "/srv/data/prog/pdbfinder2/mergepdbfinder2.pl" +
            " %s %s" % (out_file, dat_dir),
            cwd="/srv/data/prog/pdbfinder2/"
        )

        _log.debug("[pdbfinder2] compressing %s" % out_file)
        with GzipFile(gz_file, 'wb') as g:
            with open(out_file, 'rb') as f:
                while True:
                    chunk = f.read(1024)
                    if len(chunk) <= 0:
                        break
                    g.write(chunk)

class Pdbfinder2CleanupJob(Job):
    def __init__(self, mmcif_fetch_job):
        Job.__init__(self, "pdbfinder2_clean", [mmcif_fetch_job])

    def run(self):
        for datname in os.listdir(os.path.join(settings["DATADIR"], "pdbfinder2/data")):
            pdbid = datname[:4]
            if pdbfinder2_obsolete(pdbid):
                _log.warn("[pdbfinder2] removing %s" % pdbid)
                pdbfinder2_remove(pdbid)
