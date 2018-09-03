import os
import shutil
import datetime
from threading import Thread

from databanks.pdb import pdb_path, pdb_flat_path, PdbExtractJob
from databanks.structurefactors import structurefactors_path
from databanks.queue import Job
from databanks.settings import settings
from databanks.command import log_command

import logging
_log = logging.getLogger(__name__)

zata_dir = '/srv/data/zata/'

redo_script = os.path.join(zata_dir,'pdb_redo.csh')

def pdbredo_path(pdbid):
    return os.path.join(settings["DATADIR"], "pdb_redo",
                        pdbid[1:3], pdbid)

def final_path(pdbid):
    return os.path.join(pdbredo_path(pdbid),
                        '%s_final.pdb' % pdbid)

def pdbredo_uptodate(pdbid):
    in_path = structurefactors_path(pdbid)
    out_path = final_path(pdbid)
    return os.path.isfile(out_path) and (not os.path.isfile(in_path) or \
            os.path.getmtime(out_path) >= os.path.getmtime(in_path))

def pdbredo_obsolete(pdbid):
    out_path = final_path(pdbid)
    in_path = structurefactors_path(pdbid)
    return os.path.isfile(out_path) and (not os.path.isfile(in_path) or \
            os.path.getmtime(out_path) < os.path.getmtime(in_path))

def pdbredo_remove(pdbid):
    path = pdbredo_path(pdbid)
    obs_dir = os.path.join(settings["DATADIR"], "pdb_redo/obsolete")
    res_dir = os.path.join(obs_dir, pdbid)
    if os.path.isdir(path):
        if not os.path.isdir(obs_dir):
            os.mkdir(obs_dir)
        if os.path.isdir(res_dir):
            shutil.rmtree(path)
        else:
            shutil.move(path, res_dir)

class PdbredoJob(Job):
    def __init__(self, pdbid):
        Job.__init__(self, "pdbredo_%s" % pdbid)
        self._pdbid = pdbid

    def run(self):
        if not os.path.isfile(pdb_path(self._pdbid)):
            whynot_path = datetime.datetime.now().strftime(
                    '/srv/data/scratch/whynot2/comment/%Y%m%d_pdbredo.txt')
            with open(whynot_path, 'a') as f:
                f.write('COMMENT: No PDB-format coordinate file available\n')
                f.write('PDB_REDO, %s\n' % self._pdbid)
        elif not os.path.isfile(pdb_flat_path(self._pdbid)):
            PdbExtractJob(pdb_path(self._pdbid)).run()

        _log.info("[pdbredo] running pdbredo for %s" % self._pdbid)
        days = 3 * 24 * 60 * 60
        if not log_command(_log, 'pdbredo',
                           "%s %s" % (redo_script, self._pdbid),
                           timeout=days):
            _log.error("[pdbredo] pdbredo timeout for %s" % self._pdbid)

            whynot_path = os.path.join(zata_dir, 'whynot.txt')
            with open(whynot_path, 'a') as f:
                f.write(
                    'COMMENT: PDB REDO script timed out\nPDB_REDO, %s'
                    % self._pdbid
                )

        tot_path = os.path.join(pdbredo_path(self._pdbid),
                                  "%s_final_tot.pdb" % self._pdbid)
        if os.path.isfile(tot_path):
            link_path = os.path.join(settings["DATADIR"],
                                     "pdb_redo/flat/%s" % self._pdbid)
            if os.path.islink(link_path):
                os.symlink(tot_path, link_path)

class AlldataJob(Job):
    def __init__(self, fetch_pdbredo_job):
        Job.__init__(self, "pdbredo_alldata", [fetch_pdbredo_job])

    def run(self):
        log_command(_log, "pdbredo", "/srv/data/pdb_redo/alldata.csh")

class PdbredoCleanupJob(Job):
    def __init__(self, structurefactors_fetch_job):
        Job.__init__(self, "pdbredo_clean", [structurefactors_fetch_job])

    def run(self):
        for part in os.listdir(os.path.join(settings["DATADIR"],
                                            "pdb_redo")):
            partpath = os.path.join(settings["DATADIR"], "pdb_redo", part)
            if os.path.isdir(partpath) and len(part) != 2:
                for pdbid in os.listdir(partpath):
                    if pdbredo_obsolete(pdbid):
                        _log.warn("[pdbredo] removing %s" % pdbid)
                        pdbredo_remove(pdbid)
