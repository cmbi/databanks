import sys
import os
from filelock import FileLock

from databanks.queue import Queue
from databanks.whynot import WhynotCrawlJob
from databanks.pdbredo import PdbredoCleanupJob
from databanks.structurefactors import StructurefactorsCleanupJob
from databanks.data import (ScheduleMmcifDataJob, SchedulePdbDataJob,
                            SchedulePdbredoDataJob, ScheduleSceneDataJob)
from databanks.fetch import (FetchPdbJob, FetchMmcifJob, FetchNmrJob,
                             FetchStructureFactorsJob, FetchUniprotJob,
                             FetchGenbankJob, FetchGeneJob, FetchGoJob,
                             FetchEmblJob, FetchInterproJob, FetchMimmapJob,
                             FetchOmimJob, FetchOxfordJob, FetchPfamJob,
                             FetchPmcJob, FetchPrintsJob, FetchPrositeJob,
                             FetchRebaseJob, FetchRefseqJob, FetchTaxonomyJob,
                             FetchUnigeneJob, FetchEnzymeJob, FetchPdbredoJob)
from databanks.settings import settings

import logging
import logging.handlers
root = logging.getLogger()
sh = logging.StreamHandler()
handler = logging.handlers.WatchedFileHandler(filename=settings['LOGFILE'])
formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s : %(message)s')
handler.setFormatter(formatter)
sh.setFormatter(formatter)
root.addHandler(sh)
root.addHandler(handler)
sh.setLevel(logging.DEBUG)
handler.setLevel(logging.INFO)
root.setLevel(logging.DEBUG)

_log = logging.getLogger(__name__)

if __name__ == "__main__":

    lock_path = settings['LOCKFILE']
    _log.debug("waiting for lock on %s" % lock_path)
    with FileLock(lock_path) as lock:
        _log.debug("lock acquired")

        queue = Queue(settings["NTHREADS"])

        # 1. Download external data.
        # 2. Schedule jobs that work with downloaded data.
        # 3. run whynot & mrs when all data files have been
        #    generated/downloaded.
        pdb_job = FetchPdbJob()
        uniprot_job = FetchUniprotJob()
        mmcif_job = FetchMmcifJob()
        sf_job = FetchStructureFactorsJob()
        pdbredo_job = FetchPdbredoJob()
        nmr_job = FetchNmrJob()
        queue.put(uniprot_job)
        queue.put(pdb_job)
        queue.put(mmcif_job)
        queue.put(nmr_job)
        queue.put(sf_job)
        queue.put(pdbredo_job)

        queue.put(ScheduleMmcifDataJob(queue, mmcif_job, pdb_job, uniprot_job))
        queue.put(SchedulePdbDataJob(queue, pdb_job))
        queue.put(SchedulePdbredoDataJob(queue, pdbredo_job))
        queue.put(ScheduleSceneDataJob(queue, pdb_job, pdbredo_job))
        queue.put(StructurefactorsCleanupJob(sf_job, mmcif_job))
        queue.put(PdbredoCleanupJob(sf_job))

        queue.put(WhynotCrawlJob('MMCIF',
                                 os.path.join(settings["DATADIR"], "mmCIF"),
                                 [mmcif_job]), priority=10)
        queue.put(WhynotCrawlJob('PDB',
                                 os.path.join(settings["DATADIR"], "pdb/all"),
                                 [pdb_job]), priority=10)
        queue.put(WhynotCrawlJob('NMR',
                                 os.path.join(settings["DATADIR"],
                                              "nmr_restraints"),
                                 [nmr_job]), priority=10)
        queue.put(WhynotCrawlJob('STRUCTUREFACTORS',
                                 os.path.join(settings["DATADIR"],
                                              "structure_factors"),
                                 [sf_job]), priority=10)
        queue.put(WhynotCrawlJob('PDB_REDO',
                                 os.path.join(settings["DATADIR"],
                                              "pdb_redo"),
                                 [pdbredo_job]), priority=10)

        queue.put(FetchGenbankJob())
        queue.put(FetchGeneJob())
        queue.put(FetchGoJob())
        #queue.put(FetchEmblJob())
        queue.put(FetchInterproJob())
        queue.put(FetchMimmapJob())
        queue.put(FetchOmimJob())
        queue.put(FetchOxfordJob())
        queue.put(FetchPfamJob())
        queue.put(FetchPmcJob())
        queue.put(FetchPrintsJob())
        queue.put(FetchPrositeJob())
        queue.put(FetchRebaseJob())
        queue.put(FetchRefseqJob())
        queue.put(FetchTaxonomyJob())
        queue.put(FetchUnigeneJob())
        queue.put(FetchEnzymeJob())

        _log.info("runnning queue")
        queue.run()
