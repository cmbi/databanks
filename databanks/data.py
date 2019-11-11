import os

from databanks.queue import Job
from databanks.settings import settings
from databanks.dssp import (dssp_uptodate, DsspJob, dsspredo_uptodate,
                            dssp_mmcif_uptodate, DsspMmcifJob, DsspMmcifCleanupJob,
                            DsspredoJob, DsspCleanupJob, DsspredoCleanupJob)
from databanks.hssp import (hssp_uptodate, HsspJob, HsspCleanupJob)
from databanks.pdbfinder import (pdbfinder_uptodate, PdbfinderDatJob,
                                 PdbfinderJoinJob, PdbfinderCleanupJob)
from databanks.pdbfinder2 import (pdbfinder2_uptodate, Pdbfinder2DatJob,
                                  Pdbfinder2JoinJob, Pdbfinder2CleanupJob)
from databanks.pdbreport import (pdbreport_uptodate, PdbreportJob,
                                 PdbreportCleanupJob)
from databanks.bdb import (bdb_uptodate, BdbJob, BdbCleanupJob)
from databanks.pdb import (pdb_flat_uptodate, PdbExtractJob)
#from databanks.wilist import (wilist_uptodate, WilistJob, lis_types,
#                              WilistCleanupJob, wilist_failed_path)
from databanks.wilist import wilist_data_path
from databanks.hbonds import (hbonds_uptodate, HbondsJob)
from databanks.scene import (scene_uptodate, SceneJob, SceneCleanupJob,
                             lis_types as scene_types)
from databanks.pdbredo import (pdbredo_uptodate, PdbredoJob,
                               AlldataJob, PdbredoCleanupJob)
from databanks.whynot import WhynotCrawlJob, annotated_set

import logging
_log = logging.getLogger(__name__)

def list_pdbgz():
    pdb_all_dir = os.path.join(settings['DATADIR'], 'pdb/all')
    return [os.path.join(pdb_all_dir, name)
                for name in os.listdir(pdb_all_dir)
                    if name.startswith('pdb') and name.endswith('.ent.gz')]

def list_mmcif():
    mmcif_dir = os.path.join(settings['DATADIR'], 'mmCIF')
    return [os.path.join(mmcif_dir, name)
                for name in os.listdir(mmcif_dir)]

def list_pdbredo():
    pdbredo_dir = os.path.join(settings['DATADIR'], 'pdb_redo')
    paths = []
    for div in os.listdir(pdbredo_dir):
        pth = os.path.join(pdbredo_dir, div)
        if len(div) == 2 and os.path.isdir(pth):
            for entry in os.listdir(pth):
                path = os.path.join(pdbredo_dir, div, entry,
                                    '%s_final.pdb' % entry)
                if os.path.isfile(path):
                    paths.append(path)
    return paths

# Jobs may depend on other jobs, like pdbfinder2 depends on pdbfinder.
# However, a pdbfinder file may already exist and not need to run again.
# So the passed on job argument to pdbfinder2 may be None, indicating
# there's no job to wait for.


class ScheduleMmcifDataJob(Job):
    def __init__(self, queue, mmcif_fetch_job,
                              pdb_fetch_job,
                              uniprot_fetch_job):
        Job.__init__(self, "schedule_mmcif", [mmcif_fetch_job, pdb_fetch_job])
        self._queue = queue
        self._uniprot_fetch_job = uniprot_fetch_job
        self._mmcif_fetch_job = mmcif_fetch_job

    def run(self):
        _log.debug("scheduling mmcif-based data jobs")

        dssp_annotated = annotated_set('DSSP')
        hssp_annotated = annotated_set('HSSP')
        pdbfinder_annotated = annotated_set('PDBFINDER')
        pdbfinder2_annotated = annotated_set('PDBFINDER2')

        pdbfinder_jobs = []
        pdbf_clean_job = PdbfinderCleanupJob(self._mmcif_fetch_job)
        self._queue.put(pdbf_clean_job, priority=10)
        pdbfinder_jobs.append(pdbf_clean_job)

        pdbfinder2_jobs = []
        pdbf2_clean_job = Pdbfinder2CleanupJob(self._mmcif_fetch_job)
        self._queue.put(pdbf2_clean_job, priority=10)
        pdbfinder_jobs.append(pdbf2_clean_job)

        dssp_jobs = []
        dssp_clean_job = DsspMmcifCleanupJob(self._mmcif_fetch_job)
        self._queue.put(dssp_clean_job, priority=10)
        dssp_jobs.append(dssp_clean_job)

        hssp_jobs = []
        hssp_clean_job = HsspCleanupJob(self._mmcif_fetch_job)
        self._queue.put(hssp_clean_job, priority=10)
        hssp_jobs.append(hssp_clean_job)

        for mmcif_path in list_mmcif():
            pdbid = os.path.basename(mmcif_path)[:4]

            dssp_job = None
            if not dssp_mmcif_uptodate(pdbid) and pdbid not in dssp_annotated:
                _log.debug("add dssp job for %s" % pdbid)
                dssp_job = DsspMmcifJob(pdbid)
                self._queue.put(dssp_job)
                dssp_jobs.append(dssp_job)

            hssp_job = None
            if not hssp_uptodate(pdbid) and pdbid not in hssp_annotated:
                _log.debug("add hssp job for %s" % pdbid)
                hssp_job = HsspJob(pdbid, self._uniprot_fetch_job)
                self._queue.put(hssp_job, priority=1)
                hssp_jobs.append(hssp_job)

            pdbf_job = None
            if not pdbfinder_uptodate(pdbid) and pdbid not in pdbfinder_annotated:
                _log.debug("add pdbfinder job for %s" % pdbid)
                pdbf_job = PdbfinderDatJob(pdbid, dssp_job, hssp_job)
                self._queue.put(pdbf_job)
                pdbfinder_jobs.append(pdbf_job)

            if not pdbfinder2_uptodate(pdbid) and pdbid not in pdbfinder2_annotated:
                _log.debug("add pdbfinder2 job for %s" % pdbid)
                pdbf2_job = Pdbfinder2DatJob(pdbid, pdbf_job)
                self._queue.put(pdbf2_job)
                pdbfinder2_jobs.append(pdbf2_job)

        pdbfinder_join_job = PdbfinderJoinJob(pdbfinder_jobs)
        pdbfinder2_join_job = Pdbfinder2JoinJob(pdbfinder2_jobs)
        self._queue.put(pdbfinder_join_job, priority=10)
        self._queue.put(pdbfinder2_join_job, priority=10)

        self._queue.put(WhynotCrawlJob('DSSP',
                                       os.path.join(settings["DATADIR"],
                                                    "dssp-from-mmcif"),
                                       dssp_jobs), priority=10)
        self._queue.put(WhynotCrawlJob('HSSP',
                                       os.path.join(settings["DATADIR"],
                                                    "hssp"),
                                       hssp_jobs), priority=10)
        self._queue.put(WhynotCrawlJob('PDBFINDER',
                                       os.path.join(settings["DATADIR"],
                                                    "pdbfinder/PDBFIND.TXT"),
                                       [pdbfinder_join_job]), priority=10)
        self._queue.put(WhynotCrawlJob('PDBFINDER2',
                                       os.path.join(settings["DATADIR"],
                                                    "pdbfinder2/PDBFIND2.TXT"),
                                       [pdbfinder2_join_job]), priority=10)

class ScheduleSceneDataJob(Job):
    def __init__(self, queue, pdb_fetch_job, redo_fetch_job):
        Job.__init__(self, "schedule_scenes", [pdb_fetch_job, redo_fetch_job])

        self._queue = queue
        self._pdb_fetch_job = pdb_fetch_job
        self._redo_fetch_job = redo_fetch_job

    def run(self):
        for lis in scene_types:
            self._queue.put(SceneCleanupJob(self._pdb_fetch_job, 'pdb', lis))
            self._queue.put(SceneCleanupJob(self._redo_fetch_job, 'redo', lis))

        for src in ['pdb', 'redo']:
            for lis in scene_types:
                scene_annotated = annotated_set('%s_SCENES_%s' % (src.upper(), lis))
                jobs = []
                for pdbid in os.listdir(os.path.join(settings["DATADIR"], "wi-lists", src, lis)):
                    if os.path.isfile(wilist_data_path(src, lis, pdbid)) and pdbid not in scene_annotated:
                        job = SceneJob(src, lis, pdbid)
                        self._queue.put(job)
                        jobs.append(job)

                self._queue.put(WhynotCrawlJob('%s_SCENES_%s' % (src.upper(), lis),
                                               os.path.join(settings["DATADIR"],
                                                            'wi-lists/%s/scenes/%s' % (src, lis)),
                                               jobs), priority=10)


class SchedulePdbDataJob(Job):
    def __init__(self, queue, pdb_fetch_job):
        Job.__init__(self, "schedule_pdb", [pdb_fetch_job])
        self._queue = queue
        self._pdb_fetch_job = pdb_fetch_job

    def run(self):
        _log.debug("scheduling pdb-based data jobs")

        dssp_annotated = annotated_set('DSSP')
        #pdbreport_annotated = annotated_set('PDBREPORT')
        bdb_annotated = annotated_set('BDB')
        #wilist_annotated = {lis: annotated_set('WHATIF_PDB_%s' % lis)
        #                    for lis in lis_types}
        #scene_annotated = {lis: annotated_set('PDB_SCENES_%s' % lis)
        #                   for lis in scene_types}

        pdbreport_jobs = []
        #pdbreport_clean_job = PdbreportCleanupJob(self._pdb_fetch_job)
        #self._queue.put(pdbreport_clean_job, priority=10)
        #pdbreport_jobs.append(pdbreport_clean_job)

        #wilist_jobs = {}
        #for lis in lis_types:
        #    wilist_jobs[lis] = []
        #    clean_job = WilistCleanupJob(self._pdb_fetch_job, 'pdb', lis)
        #    self._queue.put(clean_job, priority=10)
        #    wilist_jobs[lis].append(clean_job)
        #
        #scene_jobs = {}
        #for lis in scene_types:
        #    scene_jobs[lis] = []
        #    clean_job = SceneCleanupJob(self._pdb_fetch_job, 'pdb', lis)
        #    self._queue.put(clean_job, priority=10)
        #    scene_jobs[lis].append(clean_job)

        #hbonds_jobs = []

        bdb_jobs = []
        bdb_clean_job = BdbCleanupJob(self._pdb_fetch_job)
        self._queue.put(bdb_clean_job, priority=10)
        bdb_jobs.append(bdb_clean_job)

        dssp_jobs = []
        dssp_clean_job = DsspCleanupJob(self._pdb_fetch_job)
        self._queue.put(dssp_clean_job, priority=10)
        dssp_jobs.append(dssp_clean_job)

        for gz_path in list_pdbgz():
            pdbid = os.path.basename(gz_path)[3:7]

            dssp_job = None
            if not dssp_uptodate(pdbid) and pdbid not in dssp_annotated:
                _log.debug("add dssp job for %s" % pdbid)
                dssp_job = DsspJob(pdbid)
                self._queue.put(dssp_job)
                dssp_jobs.append(dssp_job)

            pdb_extract_job = None
            if not pdb_flat_uptodate(pdbid):
                pdb_extract_job = PdbExtractJob(gz_path)
                self._queue.put(pdb_extract_job)

            if not bdb_uptodate(pdbid) and pdbid not in bdb_annotated:
                _log.debug("add bdb job for %s" % pdbid)
                bdb_job = BdbJob(pdbid, pdb_extract_job)
                self._queue.put(bdb_job)
                bdb_jobs.append(bdb_job)

            #if not pdbreport_uptodate(pdbid) and pdbid not in pdbreport_annotated:
            #    _log.debug("add pdbreport job for %s" % pdbid)
            #    pdbreport_job = PdbreportJob(pdbid, pdb_extract_job)
            #    self._queue.put(pdbreport_job, priority=1)
            #    pdbreport_jobs.append(pdbreport_job)

            #for lis in lis_types:
            #    wilist_job = None
            #    if not wilist_uptodate('pdb', lis, pdbid) and pdbid not in wilist_annotated[lis] and \
            #            not os.path.isfile(wilist_failed_path('pdb', lis, pdbid)):
            #        _log.debug("add pdb wilist job for %s" % pdbid)
            #        wilist_job = WilistJob('pdb', lis, pdbid, pdb_extract_job)
            #        self._queue.put(wilist_job)
            #        wilist_jobs[lis].append(wilist_job)
            #
            #    if lis in scene_types and not scene_uptodate('pdb', lis, pdbid) and \
            #            pdbid not in scene_annotated[lis]:
            #        _log.debug("add pdb scene job for %s" % pdbid)
            #        scene_job = SceneJob('pdb', lis, pdbid, wilist_job)
            #        self._queue.put(scene_job)
            #        scene_jobs[lis].append(scene_job)
            #
            #if not hbonds_uptodate(pdbid):
            #    _log.debug("add hbonds job for %s" % pdbid)
            #    hbonds_job = HbondsJob(pdbid, pdb_extract_job)
            #    self._queue.put(hbonds_job)
            #    hbonds_jobs.append(hbonds_job)

        self._queue.put(WhynotCrawlJob('BDB',
                                       os.path.join(settings["DATADIR"],
                                                    'bdb'),
                                       bdb_jobs), priority=10)
        self._queue.put(WhynotCrawlJob('PDBREPORT',
                                       os.path.join(settings["DATADIR"],
                                                    'pdbreport'),
                                       pdbreport_jobs), priority=10)
        #for lis in lis_types:
        #    self._queue.put(WhynotCrawlJob('WHATIF_PDB_%s' % lis,
        #                                   os.path.join(
        #                                       settings["DATADIR"],
        #                                       'wi-lists/pdb/%s' % lis
        #                                   ),
        #                                   wilist_jobs[lis]), priority=10)
        #for lis in scene_types:
        #    self._queue.put(WhynotCrawlJob(
        #                        'PDB_SCENES_%s' % lis,
        #                         os.path.join(
        #                             settings["DATADIR"],
        #                             'wi-lists/pdb/scenes/%s' % lis
        #                         ),
        #                         scene_jobs[lis]), priority=10)


class SchedulePdbredoDataJob(Job):
    def __init__(self, queue, pdbredo_fetch_job):
        Job.__init__(self, "schedule_pdbredo", [pdbredo_fetch_job])
        self._queue = queue
        self._pdbredo_fetch_job = pdbredo_fetch_job

    def run(self):
        _log.debug("scheduling pdbredo-based data jobs")

        pdbredo_annotated = annotated_set('PDB_REDO')
        dsspredo_annotated = annotated_set('DSSP_REDO')
        #wilist_annotated = {lis: annotated_set('WHATIF_REDO_%s' % lis)
        #                    for lis in lis_types}
        #scene_annotated = {lis: annotated_set('REDO_SCENES_%s' % lis)
        #                   for lis in scene_types}

        dsspredo_jobs = []
        dsspredo_clean_job = DsspredoCleanupJob(self._pdbredo_fetch_job)
        self._queue.put(dsspredo_clean_job, priority=10)
        dsspredo_jobs.append(dsspredo_clean_job)

        #wilist_jobs = {}
        #for lis in lis_types:
        #    wilist_jobs[lis] = []
        #    clean_job = WilistCleanupJob(self._pdbredo_fetch_job, 'redo', lis)
        #    self._queue.put(clean_job, priority=10)
        #    wilist_jobs[lis].append(clean_job)
        #
        #scene_jobs = {}
        #for lis in scene_types:
        #    scene_jobs[lis] = []
        #    clean_job = SceneCleanupJob(self._pdbredo_fetch_job, 'redo', lis)
        #    self._queue.put(clean_job, priority=10)
        #    scene_jobs[lis].append(clean_job)

        for pdbredo_path in list_pdbredo():
            pdbid = os.path.basename(pdbredo_path)[:4]

            if not dsspredo_uptodate(pdbid) and pdbid not in dsspredo_annotated:
                _log.debug("add dsspredo job for %s" % pdbid)
                dsspredo_job = DsspredoJob(pdbid, self._pdbredo_fetch_job)
                self._queue.put(dsspredo_job)
                dsspredo_jobs.append(dsspredo_job)

            #for lis in lis_types:
            #    wilist_job = None
            #    if not wilist_uptodate('redo', lis, pdbid) and \
            #            pdbid not in wilist_annotated[lis] and \
            #            not os.path.isfile(wilist_failed_path('redo', lis, pdbid)):
            #        _log.debug("add redo wilist job for %s" % pdbid)
            #        wilist_job = WilistJob('redo', lis, pdbid, self._pdbredo_fetch_job)
            #        self._queue.put(wilist_job)
            #        wilist_jobs[lis].append(wilist_job)
            #
            #    if lis in scene_types and not scene_uptodate('redo', lis, pdbid) and \
            #            pdbid not in scene_annotated[lis]:
            #        _log.debug("add redo scene job for %s" % pdbid)
            #        scene_job = SceneJob('redo', lis, pdbid, wilist_job)
            #        self._queue.put(scene_job)
            #        scene_jobs[lis].append(scene_job)

        self._queue.put(AlldataJob(self._pdbredo_fetch_job))
        self._queue.put(WhynotCrawlJob('DSSP_REDO',
                                       os.path.join(settings["DATADIR"],
                                                    'dssp_redo'),
                                       dsspredo_jobs), priority=10)
        #for lis in lis_types:
        #    self._queue.put(WhynotCrawlJob('WHATIF_REDO_%s' % lis,
        #                                   os.path.join(
        #                                       settings["DATADIR"],
        #                                       'wi-lists/redo/%s' % lis
        #                                   ),
        #                                   wilist_jobs[lis]), priority=10)
        #for lis in scene_types:
        #    self._queue.put(WhynotCrawlJob(
        #                        'REDO_SCENES_%s' % lis,
        #                        os.path.join(
        #                            settings["DATADIR"],
        #                            'wi-lists/redo/scenes/%s' % lis
        #                        ),
        #                        scene_jobs[lis]), priority=10)


