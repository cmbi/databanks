import os
import re
import shutil
from glob import glob
from threading import current_thread
from bz2 import BZ2File
from datetime import datetime

from databanks.queue import Job
from databanks.settings import settings
from databanks.command import log_command
from databanks.pdb import pdb_path, pdb_flat_path

import logging
_log = logging.getLogger(__name__)

#whatif = "/srv/data/prog/wi-lists/whatif/src/whatif"
whatcheck = "/srv/data/zata/whatcheck14/bin/whatcheck"
htmlgen = "/srv/data/zata/whatcheck14/dbdata/pdbout2html"
ccp4setup = "/srv/data/zata/ccp4-7.0/bin/ccp4.setup-sh"

def pdbreport_path(pdbid):
    return os.path.join(settings["DATADIR"], "pdbreport",
                        pdbid[1:3], pdbid)

p_html_img = re.compile(r"\<(img|IMG) (src|SRC)=(.+?)\/?\>")

# SLOW!
def pdbreport_complete(dir_path):
    index_path = os.path.join(dir_path, "index.html")
    if not os.path.isfile(index_path):
        return False

    with open(index_path, 'r') as f:
        for line in f:
            m = p_html_img.search(line)
            if m:
                img_name = m.group(3)
                # unquote:
                if img_name[0] == '\"' and img_name[-1] == '\"':
                    img_name = img_name[1:-1]

                img_path = os.path.join(dir_path, img_name)
                if not os.path.isfile(img_path):
                    return False

    check_path = os.path.join(dir_path, "check.db.bz2")
    if not os.path.isfile(check_path):
        return False

    return True

def pdbreport_uptodate(pdbid):
    in_path = pdb_path(pdbid)
    out_dir = pdbreport_path(pdbid)
    index_path = os.path.join(out_dir, "index.html")
    return os.path.isfile(index_path) and \
            os.path.getmtime(index_path) >= os.path.getmtime(in_path)

def pdbreport_obsolete(pdbid):
    paths = glob(os.path.join(settings["DATADIR"],
                              "pdbreport/??", pdbid))
    if len(paths) <= 0:
        return False
    out_path = os.path.join(paths[0], "index.html")
    in_path = pdb_path(pdbid)
    return os.path.isfile(out_path) and not os.path.isfile(in_path)

def pdbreport_remove(pdbid):
    path = pdbreport_path(pdbid)
    obs_dir = os.path.join(settings["DATADIR"], "pdbreport/obsolete")
    res_dir = os.path.join(obs_dir, pdbid)
    if os.path.isdir(path):
        if not os.path.isdir(obs_dir):
            os.mkdir(obs_dir)
        if os.path.isdir(res_dir):
            shutil.rmtree(path)
        else:
            shutil.move(path, res_dir)

def valid_html(path):
    with open(path, 'r') as f:
        for line in f:
            if "Final summary" in line:
                return True
    return False

def log_to_whynot(log_path, pdbid, whynot_path):
    with open(whynot_path, 'w') as w:
        with open(log_path, 'r') as l:
            hit = False
            for line in l:
                if "No protein/DNA/RNA read from input file" in line:
                    w.write("COMMENT: Too few normal (amino or nucleic acid) residues found\n")
                    hit = True
                    break
                elif "STRUCTURE FAR TOO BAD" in line:
                    w.write("COMMENT: Just too bad\n")
                    hit = True
                    break
                elif "You overloaded the soup" in line:
                    w.write("COMMENT: Just too big\n")
                    hit = True
                    break
                elif "Too many backbone atoms have zero occupancy" in line:
                    w.write("COMMENT: Too few normal (amino or nucleic acid) residues found\n")
                    hit = True
                    break
            if not hit:
                w.write("COMMENT: WHAT_CHECK: general error\n")
            w.write("PDBREPORT,%s" % pdbid)


class PdbreportJob(Job):
    def __init__(self, pdbid, pdb_extract_job=None):
        deps = []
        if pdb_extract_job is not None:
            deps.append(pdb_extract_job)
        Job.__init__(self, "pdbreport_%s" % pdbid, deps)
        self._pdbid = pdbid
        self._out_dir = os.path.join(settings["DATADIR"], "pdbreport",
                                     self._pdbid[1:3], self._pdbid)

    def run(self):
        in_path = pdb_flat_path(self._pdbid)
        if not os.path.isfile(in_path):
            return

        out_dir = pdbreport_path(self._pdbid)
        if not os.path.isdir(out_dir):
            os.mkdir(out_dir)

        log_path = os.path.join(out_dir, "log.log")

        txt_path = os.path.join(out_dir, "pdbout.txt")
        check_path = os.path.join(out_dir, "check.db")
        checkbz2_path = os.path.join(out_dir, "check.db.bz2")
        html_path = os.path.join(out_dir, "pdbout.html")
        index_path = os.path.join(out_dir, "index.html")
        ion_path = os.path.join(out_dir, "%s.ion" % self._pdbid)
        ionout_path = os.path.join(out_dir, "pdb%s_ION.OUT" % self._pdbid)

        whynot_path = ("/srv/data/scratch/whynot2/comment/%sWC.txt"
                       % (datetime.now().strftime("%G%m%d")))

        if log_command(_log, 'pdbreport', ". %s; %s %s" % (ccp4setup,
                                                           whatcheck,
                                                           in_path),
                       cwd=out_dir, timeout=5 * 60):
            if os.path.isfile(txt_path):
                log_command(_log, 'pdbreport', htmlgen,
                            cwd=out_dir)
                if os.path.isfile(html_path) and valid_html(html_path):
                    os.rename(html_path, index_path)
                else:
                    _log.debug("validation failed")
                    if os.path.isfile(log_path):
                        log_to_whynot(log_path, self._pdbid, whynot_path)

                if os.path.isfile(check_path):
                    with BZ2File(checkbz2_path, 'wb') as g:
                        with open(check_path, 'rb') as f:
                            while True:
                                chunk = f.read(1024)
                                if len(chunk) <= 0:
                                    break
                                g.write(chunk)
                    os.remove(check_path)

                if os.path.isfile(ionout_path):
                    os.rename(ionout_path, ion_path)
            else:
                _log.debug("validation failed")
                if os.path.isfile(log_path):
                    log_to_whynot(log_path, self._pdbid, whynot_path)
        else:
            _log.error("[pdbreport] whatcheck timeout for %s" % self._pdbid)

class PdbreportCleanupJob(Job):
    def __init__(self, pdb_fetch_job):
        Job.__init__(self, "pdbreport_clean", [pdb_fetch_job])

    def run(self):
        for part in os.listdir(os.path.join(settings["DATADIR"], "pdbreport")):
            partpath = os.path.join(settings["DATADIR"], "pdbreport", part)
            if len(part) == 2 and os.path.isdir(partpath):
                for pdbid in os.listdir(partpath):
                    if pdbreport_obsolete(pdbid):
                        _log.warn("[pdbreport] removing %s" % pdbid)
                        pdbreport_remove(pdbid)
