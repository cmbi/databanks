import os
import shutil
import commands
import tempfile
from bz2 import BZ2File
from threading import current_thread

from databanks.settings import settings
from databanks.queue import Job
from databanks.command import log_command
from databanks.pdb import pdb_flat_path, pdb_path

import logging
_log = logging.getLogger(__name__)

whatif = "/srv/data/prog/wi-lists/whatif/src/whatif"

def hbonds_path(pdbid):
    return os.path.join(settings["DATADIR"], "wi-lists/pdb/hb2", pdbid)

def hbonds_uptodate(pdbid):
    in_path = pdb_path(pdbid)
    dir_path = hbonds_path(pdbid)
    log_path = os.path.join(dir_path, "%s.hb2.bz2" % pdbid)
    return os.path.isfile(log_path) and \
            os.path.getmtime(log_path) >= os.path.getmtime(in_path)

def hbonds_obsolete(pdbid):
    out_path = os.path.join(hbonds_path(pdbid),
                           "%s.hb2.bz2" % pdbid)
    in_path = pdb_path(pdbid)
    return os.path.isfile(out_path) and not os.path.isfile(in_path)

def hbonds_remove(pdbid):
    shutil.rmtree(hbonds_path(pdbid))

class HbondsJob(Job):
    def __init__(self, pdbid, pdb_extract_job=None):
        if pdb_extract_job is None:
            Job.__init__(self, "hbonds_%s" % pdbid)
        else:
            Job.__init__(self, "hbonds_%s" % pdbid, [pdb_extract_job])
        self._pdbid = pdbid

    def run(self):
        in_path = pdb_flat_path(self._pdbid)
        if not os.path.isfile(in_path):
            return

        out_dir = hbonds_path(self._pdbid)
        if not os.path.isdir(out_dir):
            os.mkdir(out_dir)

        _log.info("making hbonds for %s" % self._pdbid)

        logfilename = "%s.hb2.log" % self._pdbid
        script = """
                 GETMOL %s Y %s
                 HBONDS
                 HB2INI

                 DOLOG %s 0
                 HBONDS
                 HB2LIS protein 0 protein 0
                 NOLOG
                 FULLST Y
                 """ % (in_path, self._pdbid, logfilename)
        try:
            tmpdir = tempfile.mkdtemp()
            if log_command(_log, 'hbonds', whatif,
                           cwd=tmpdir, timeout=20, strin=script):

                logfilepath = os.path.join(tmpdir, logfilename)
                out_path = os.path.join(out_dir, "%s.hb2.bz2" % self._pdbid)

                with open(logfilepath, 'r') as g:
                    with BZ2File(out_path, 'wb') as f:
                        for line in g.readlines()[2:]:
                            f.write(line.replace("->", "-"))
            else:
                _log.error("[hbonds] whatif timeout for %s" % self._pdbid)
        finally:
            # Remove all whatif runtime files
            if os.path.isdir(tmpdir):
                shutil.rmtree(tmpdir)
