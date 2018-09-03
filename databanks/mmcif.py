import os

from databanks.settings import settings

def mmcif_path(pdbid):
    return os.path.join(settings["DATADIR"], "mmCIF/%s.cif.gz" % pdbid)
