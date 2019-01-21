import os
from databanks.settings import settings
from databanks.mmcif import mmcif_path


def structurefactors_path(pdbid):
    return os.path.join(settings["DATADIR"],
                        "structure_factors/r%ssf.ent.gz" % pdbid)

def structurefactors_obsolete(pdbid):
    out_path = structurefactors_path(pdbid)
    in_path = mmcif_path(pdbid)
    return os.path.isfile(out_path) and not os.path.isfile(in_path)

def structurefactors_remove(pdbid):
    path = structurefactors_path(pdbid)
    if os.path.isfile(path):
        os.remove(path)


class StructurefactorsCleanupJob(Job):
    def __init__(self, structurefactors_fetch_job, mmcif_fetch_job):
        Job.__init__(self, "sf_clean", [structurefactors_fetch_job, mmcif_fetch_job])

    def run(self):
        for filename in os.listdir(os.path.join(settings["DATADIR"],
                                                "structure_factors")):
            pdbid = filename[1:5]

            if structurefactors_obsolete(pdbid):
                _log.warn("[structure factors] removing %s" % pdbid)
                structurefactors_remove(pdbid)
