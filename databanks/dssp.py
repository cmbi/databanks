import os

from databanks.queue import Job
from databanks.settings import settings
from databanks.mmcif import mmcif_path
from databanks.pdb import pdb_path
from databanks.pdbredo import pdbredo_path, final_path
from databanks.command import log_command

import logging
_log = logging.getLogger(__name__)


MKDSSP = '/usr/local/bin/mkdssp'

def dssp_mmcif_path(pdbid):
    return os.path.join(settings["DATADIR"], "dssp-from-mmcif/%s.dssp" % pdbid)

def dssp_path(pdbid):
    return os.path.join(settings["DATADIR"], "dssp/%s.dssp" % pdbid)

def dsspredo_path(pdbid):
    return os.path.join(settings["DATADIR"], "dssp_redo/%s.dssp" % pdbid)

def dssp_obsolete(pdbid):
    out_path = dssp_path(pdbid)
    in_path = pdb_path(pdbid)
    return os.path.isfile(out_path) and not os.path.isfile(in_path)

def dssp_mmcif_obsolete(pdbid):
    out_path = dssp_mmcif_path(pdbid)
    in_path = mmcif_path(pdbid)
    return os.path.isfile(out_path) and not os.path.isfile(in_path)

def dsspredo_obsolete(pdbid):
    out_path = dsspredo_path(pdbid)
    in_path = final_path(pdbid)
    return os.path.isfile(out_path) and not os.path.isfile(in_path)

def dssp_remove(pdbid):
    path = dssp_path(pdbid)
    if os.path.isfile(path):
        os.remove(path)

def dssp_mmcif_remove(pdbid):
    path = dssp_mmcif_path(pdbid)
    if os.path.isfile(path):
        os.remove(path)

def dsspredo_remove(pdbid):
    path = dsspredo_path(pdbid)
    if os.path.isfile(path):
        os.remove(path)

def dssp_mmcif_uptodate(pdbid):
    in_path = mmcif_path(pdbid)
    out_path = dssp_mmcif_path(pdbid)
    return os.path.isfile(out_path) and \
        os.path.getmtime(out_path) >= os.path.getmtime(in_path)

def dssp_uptodate(pdbid):
    in_path = pdb_path(pdbid)
    out_path = dssp_path(pdbid)
    return os.path.isfile(out_path) and \
        os.path.getmtime(out_path) >= os.path.getmtime(in_path)

def dsspredo_uptodate(pdbid):
    in_path = final_path(pdbid)
    out_path = dsspredo_path(pdbid)
    return os.path.isfile(out_path) and (not os.path.isfile(in_path) or \
        os.path.getmtime(out_path) >= os.path.getmtime(in_path))

class DsspJob(Job):
    def __init__(self, pdbid):
        Job.__init__(self, "dssp_%s" % pdbid)
        self._pdbid = pdbid

    def run(self):
        in_path = pdb_path(self._pdbid)
        out_path = dssp_path(self._pdbid)

        if os.path.isfile(in_path):
            log_command(_log, 'dssp', "%s %s %s" % (MKDSSP, in_path, out_path))

class DsspMmcifJob(Job):
    def __init__(self, pdbid):
        Job.__init__(self, "dssp_mmcif_%s" % pdbid)
        self._pdbid = pdbid

    def run(self):
        in_path = mmcif_path(self._pdbid)
        out_path = dssp_mmcif_path(self._pdbid)

        if os.path.isfile(in_path):
            log_command(_log, 'dssp-from-mmcif', "%s %s %s" % (MKDSSP, in_path, out_path))

class DsspredoJob(Job):
    def __init__(self, pdbid, pdbredo_job=None):
        if pdbredo_job is None:
            Job.__init__(self, "dsspredo_%s" % pdbid, [])
        else:
            Job.__init__(self, "dsspredo_%s" % pdbid, [pdbredo_job])
        self._pdbid = pdbid

    def run(self):
        in_path = final_path(self._pdbid)
        out_path = dsspredo_path(self._pdbid)

        if os.path.isfile(in_path):
            log_command(_log, 'dssp', "%s %s %s" % (MKDSSP, in_path, out_path))

class DsspMmcifCleanupJob(Job):
    def __init__(self, mmcif_fetch_job):
        Job.__init__(self, "dssp_mmcif_clean", [mmcif_fetch_job])

    def run(self):
        for dsspname in os.listdir(os.path.join(settings["DATADIR"], "dssp-from-mmcif")):
            pdbid = dsspname[:4]
            if dssp_mmcif_obsolete(pdbid):
                _log.warn("[dssp-from-mmcif] removing %s" % pdbid)
                dssp_mmcif_remove(pdbid)

class DsspCleanupJob(Job):
    def __init__(self, pdb_fetch_job):
        Job.__init__(self, "dssp_clean", [pdb_fetch_job])

    def run(self):
        for dsspname in os.listdir(os.path.join(settings["DATADIR"], "dssp")):
            pdbid = dsspname[:4]
            if dssp_obsolete(pdbid):
                _log.warn("[dssp] removing %s" % pdbid)
                dssp_remove(pdbid)
            if dssp_mmcif_obsolete(pdbid):
                _log.warn("[dssp] removing %s" % pdbid)
                dssp_mmcif_remove(pdbid)

class DsspredoCleanupJob(Job):
    def __init__(self, structurefactors_fetch_job):
        Job.__init__(self, "dsspredo_clean", [structurefactors_fetch_job])

    def run(self):
        for dsspname in os.listdir(os.path.join(settings["DATADIR"], "dssp_redo")):
            pdbid = dsspname[:4]
            if dsspredo_obsolete(pdbid):
                _log.warn("[dsspredo] removing %s" % pdbid)
                dsspredo_remove(pdbid)
