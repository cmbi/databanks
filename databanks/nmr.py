import os
from databanks.settings import settings
from databanks.pdb import pdb_path

def nmr_path(pdbid):
    return os.path.join(settings["DATADIR"],
                        "nmr_restraints/%s.mr.gz" % pdbid)

def nmr_obsolete(pdbid):
    out_path = nmr_path(pdbid)
    in_path = pdb_path(pdbid)
    return os.path.isfile(out_path) and not os.path.isfile(in_path)

def nmr_remove(pdbid):
    path = nmr_path(pdbid)
    if os.path.isfile(path):
        os.remove(path)
