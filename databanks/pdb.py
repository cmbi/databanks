import os
import shutil
from gzip import GzipFile

from databanks.mmcif import mmcif_path
from databanks.queue import Job
from databanks.settings import settings


import logging
_log = logging.getLogger(__name__)

def pdb_path(pdbid):
    return os.path.join(settings["DATADIR"], "pdb/all/pdb%s.ent.gz" % pdbid)

def pdb_flat_path(pdbid):
    gz_path = pdb_path(pdbid)
    flat_path = gz_path.replace(".ent.gz", ".ent").replace("/all/", "/flat/")
    return flat_path

def pdb_flat_uptodate(pdbid):
    gz_path = pdb_path(pdbid)
    flat_path = pdb_flat_path(pdbid)
    return os.path.isfile(pdb_flat_path(pdbid)) and \
            os.path.getmtime(flat_path) >= os.path.getmtime(gz_path)

def pdb_obsolete(pdbid):
    return os.path.isfile(pdb_path(pdbid)) and not os.path.isfile(mmcif_path(pdbid))

def pdb_remove(pdbid):
    for path in [pdb_path(pdbid), pdb_flat_path(pdbid)]:
        if os.path.isfile(path):
            os.remove(path)

class PdbExtractJob(Job):
    def __init__(self, gz_path):
        self._pdbid = os.path.basename(gz_path)[3:7]

        Job.__init__(self, "pdb_extract_%s" % self._pdbid)

        self._gz_path = gz_path
        self._out_path = os.path.join(settings['DATADIR'],
                                      'pdb/flat/pdb%s.ent' % self._pdbid)

    def run(self):
        _log.info("extract pdb for %s" % self._pdbid)

        with GzipFile(self._gz_path, 'rb') as f:
            with open(self._out_path, 'wb') as g:
                while True:
                    chunk = f.read(1024)
                    if len(chunk) <= 0:
                        break
                    g.write(chunk)
        shutil.copystat(self._gz_path, self._out_path)

class PdbCleanupJob(Job):
    def __init__(self, pdb_fetch_job):
        Job.__init__(self, "pdb_clean", [pdb_fetch_job])

    def run(self):
        for flatname in os.listdir(os.path.join(settings["DATADIR"], "pdb/flat")):
            pdbid = flatname[3:7]
            if pdb_obsolete(pdbid) or not os.path.isfile(pdb_path(pdbid)):
                _log.warn("[pdb] removing %s" % pdbid)
                pdb_remove(pdbid)
