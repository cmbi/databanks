import os
from bz2 import BZ2File
from subprocess import Popen, PIPE

from databanks.queue import Job
from databanks.settings import settings
from databanks.mmcif import mmcif_path
from databanks.pdb import pdb_path
from databanks.command import log_command

import logging
_log = logging.getLogger(__name__)

MKHSSP = '/usr/local/bin/mkhssp'
HSSPCONV = '/usr/local/bin/hsspconv'

def find_input(pdbid):
    cif_path = mmcif_path(pdbid)
    p_path = pdb_path(pdbid)
    if os.path.isfile(p_path):
        return p_path
    else:
        return cif_path

def is_empty_file(path):
    if os.path.getsize(path) <= 0:
        return True

    with BZ2File(path, 'r') as f:
        return len(f.read()) <= 0

def hssp_uptodate(pdbid):
    in_path = mmcif_path(pdbid)
    out_path = hssp1_path(pdbid)

    return os.path.isfile(out_path) and \
        os.path.getmtime(out_path) >= os.path.getmtime(in_path) and \
        not is_empty_file(out_path)

def hssp3_path(pdbid):
    return os.path.join(settings["DATADIR"],
                        "hssp3/%s.hssp.bz2" % pdbid)

def hssp1_path(pdbid):
    return os.path.join(settings["DATADIR"],
                        "hssp/%s.hssp.bz2" % pdbid)

def hssp_obsolete(pdbid):
    out_path = hssp1_path(pdbid)
    in_path = mmcif_path(pdbid)
    return os.path.isfile(out_path) and not os.path.isfile(in_path)

def hssp_remove(pdbid):
    for path in [hssp3_path(pdbid), hssp1_path(pdbid)]:
        if os.path.isfile(path):
            os.remove(path)

def hg_fasta_path(seq_id):
    return os.path.join(settings["DATADIR"],
                        'hg-fasta/%s.fasta' % seq_id)

def hg_hssp_path(seq_id):
    return os.path.join(settings["DATADIR"],
                        'hg-hssp/%s.sto.bz2' % seq_id)

class HgHsspJob(Job):
    def __init__(self, seq_id):
        Job.__init__(self, "hghssp_%s" % seq_id, [])
        self._seq_id = seq_id

    def run(self):
        in_path = hg_fasta_path(self._seq_id)
        out_path = hg_hssp_path(self._seq_id)

        cmd = [MKHSSP, '-i', in_path, '-o', out_path,
               '-a', '1', '-m', '2500', '--fetch-dbrefs',
               '-d', os.path.join(settings["DATADIR"],
                                  'fasta/uniprot_sprot.fasta'),
               '-d', os.path.join(settings["DATADIR"],
                                  'fasta/uniprot_trembl.fasta')]

        if os.path.isfile(in_path):
            _log.debug("[hghssp] %s" % ' '.join(cmd))
            p = Popen(cmd, stderr=PIPE, stdout=PIPE)
            p.wait()
            while True:
                out_line = p.stdout.readline()
                if out_line:
                    log.debug("[hghssp] %s" % out_line.strip())
                err_line = p.stderr.readline()
                if err_line:
                    log.error("[hghssp] %s" % err_line.strip())
                if not out_line and not err_line:
                    break


class HsspJob(Job):
    def __init__(self, pdbid, fetch_uniprot_job=None):
        if fetch_uniprot_job is None:
            Job.__init__(self, "hssp_%s" % pdbid, [])
        else:
            Job.__init__(self, "hssp_%s" % pdbid, [fetch_uniprot_job])
        self._pdbid = pdbid

    def run(self):
        in_path = find_input(self._pdbid)
        out3_path = hssp3_path(self._pdbid)
        out1_path = hssp1_path(self._pdbid)
        err_path = "/srv/data/scratch/whynot2/hssp/%s.err" % self._pdbid

        cmd = [MKHSSP, '-i', in_path, '-o', out3_path,
               '-a', '1', '-m', '2500', '--fetch-dbrefs',
               '-d', os.path.join(settings["DATADIR"],
                                  'fasta/uniprot_sprot.fasta'),
               '-d', os.path.join(settings["DATADIR"],
                                  'fasta/uniprot_trembl.fasta')]

        if os.path.isfile(in_path):
            _log.debug("[hssp] %s" % ' '.join(cmd))
            with open(err_path, 'w') as f:
                p = Popen(cmd, stderr=f, stdout=PIPE)
                p.wait()
                for line in p.stdout:
                    _log.debug("[hssp] %s" % line.strip())

        if os.path.isfile(out3_path):
            log_command(_log, 'hssp',
                "%s %s %s" %(HSSPCONV, out3_path, out1_path)
            )
            if os.path.isfile(err_path):
                os.remove(err_path)

class HsspCleanupJob(Job):
    def __init__(self, mmcif_fetch_job):
        Job.__init__(self, "hssp_clean", [mmcif_fetch_job])

    def run(self):
        for hsspname in os.listdir(os.path.join(settings["DATADIR"],
                                                "hssp")):
            pdbid = hsspname[:4]
            if hssp_obsolete(pdbid):
                _log.warn("[hssp] removing %s" % pdbid)
                hssp_remove(pdbid)
