import os
import shutil
from bz2 import BZ2File

from databanks.pdb import pdb_path
from databanks.structurefactors import structurefactors_path
from databanks.pdbredo import final_path
from databanks.settings import settings
from databanks.queue import Job
from databanks.command import log_command

import logging
_log = logging.getLogger(__name__)


lis_types = ['acc', 'cal', 'cc1', 'cc2', 'cc3', 'chi', 'dsp', 'iod', 'sbh',
             'sbr', 'ss1', 'ss2', 'tau', 'wat']

whatif = "/srv/data/prog/wi-lists/whatif/src/whatif"


def wilist_path(src, lis_type, pdbid):
    return os.path.join(settings["DATADIR"], "wi-lists", src, lis_type, pdbid)

def wilist_data_path(src, lis_type, pdbid):
    return os.path.join(wilist_path(src, lis_type, pdbid),
                        "%s.%s.bz2" % (pdbid, lis_type))

def wilist_failed_path(src, lis_type, pdbid):
    return os.path.join(wilist_path(src, lis_type, pdbid), 'failed')

def wilist_uptodate(src, lis_type, pdbid):
    if src.lower() == 'pdb':
        in_path = pdb_path(pdbid)
    elif src.lower() == 'redo':
        in_path = structurefactors_path(pdbid)
    else:
        raise Exception("unknown structure type: %s" % src)

    dir_path = wilist_path(src, lis_type, pdbid)
    file_path = os.path.join(dir_path, "%s.%s.bz2" % (pdbid, lis_type))
    whatif_path = os.path.join(dir_path, "%s.%s.whynot" % (pdbid, lis_type))

    for path in [file_path, whatif_path]:
        if os.path.isfile(path) and os.path.isfile(in_path) and \
                os.path.getmtime(path) > os.path.getmtime(in_path):
            return True
    return False

def wilist_obsolete(src, lis_type, pdbid):
    if src.lower() == 'pdb':
        in_path = pdb_path(pdbid)
    elif src.lower() == 'redo':
        in_path = final_path(pdbid)
    else:
        raise Exception("unknown structure type: %s" % src)

    out_path = wilist_data_path(src, lis_type, pdbid)

    return os.path.isfile(out_path) and not os.path.isfile(in_path)

def wilist_remove(src, lis_type, pdbid):
    path = wilist_path(src, lis_type, pdbid)
    if os.path.isdir(path):
        shutil.rmtree(path)

class WilistJob(Job):
    def __init__(self, src, lis_type, pdbid, structure_job=None):
        if structure_job is None:
            Job.__init__(self, "wilist_%s_%s_%s" % (src, lis_type, pdbid), [])
        else:
            Job.__init__(self, "wilist_%s_%s_%s" % (src, lis_type, pdbid), [structure_job])
        self._src = src
        self._lis_type = lis_type
        self._pdbid = pdbid

    def run(self):
        out_dir = wilist_path(self._src, self._lis_type, self._pdbid)
        if not os.path.isdir(out_dir):
            os.mkdir(out_dir)
        flag = ''
        if self._src.lower() == 'redo':
            flag = 'setwif 498 2'
        if not log_command(_log, 'wilist',
                           "%s %s lists lis%s %s fullst Y" % (whatif, flag,
                                                              self._lis_type,
                                                              self._pdbid),
                           cwd=out_dir, timeout=20):
            _log.error("[wilist] whatif timeout for %s %s %s" % (self._src,
                                                                 self._lis_type,
                                                                 self._pdbid))
        # Remove whatif runtime files:
        # (remove everything but the list or whynot file)
        for filename in os.listdir(out_dir):
            if not filename.startswith("%s.%s" % (self._pdbid, self._lis_type)):
                os.remove(os.path.join(out_dir, filename))

        # bzip2 the file, if not already.
        list_path = os.path.join(out_dir, "%s.%s" % (self._pdbid, self._lis_type))
        bz2_path = list_path + ".bz2"
        if os.path.isfile(list_path):
            if not os.path.isfile(bz2_path):
                with BZ2File(bz2_path, 'wb') as g:
                    with open(list_path, 'rb') as f:
                        while True:
                            chunk = f.read(1024)
                            if len(chunk) <= 0:
                                break
                            g.write(chunk)
            os.remove(list_path)

        if not os.path.isfile(list_path) and not os.path.isfile(bz2_path):
            with open(wilist_failed_path(self._src, self._lis_type, self._pdbid), 'w') as f:
                f.write('')

class WilistCleanupJob(Job):
    def __init__(self, fetch_job, src, lis_type):
        Job.__init__(self, "wilist_clean_%s_%s"  % (src, lis_type), [fetch_job])
        self._src = src
        self._lis_type = lis_type

    def run(self):
        for pdbid in os.listdir(os.path.join(settings["DATADIR"],
                                             "wi-lists", self._src, self._lis_type)):
            if wilist_obsolete(self._src, self._lis_type, pdbid):
                _log.warn("[wilist] removing %s %s %s" % (self._src, self._lis_type, pdbid))
                wilist_remove(self._src, self._lis_type, pdbid)
