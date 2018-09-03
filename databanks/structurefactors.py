import os
from databanks.settings import settings
from databanks.pdb import pdb_path


def structurefactors_path(pdbid):
    return os.path.join(settings["DATADIR"],
                        "structure_factors/r%ssf.ent.gz" % pdbid)

def structurefactors_obsolete(pdbid):
    out_path = structurefactors_path(pdbid)
    in_path = pdb_path(pdbid)
    return os.path.isfile(out_path) and not os.path.isfile(in_path)

def structurefactors_remove(pdbid):
    path = structurefactors_path(pdbid)
    if os.path.isfile(path):
        os.remove(path)
