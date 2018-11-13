import os
import shutil

from databanks.pdb import pdb_path
from databanks.structurefactors import structurefactors_path
from databanks.pdbredo import pdbredo_path, final_path
from databanks.wilist import wilist_data_path
from databanks.settings import settings
from databanks.queue import Job
from databanks.command import log_command

import logging
_log = logging.getLogger(__name__)

lis_types = ['ss2', 'iod']
lis_names = {'ss2': 'sym-contacts',
             'iod': 'ion-sites'}
commands = {'ss2': 'symm',
            'iod': 'ion'}

script = "/usr/local/bin/scenes"
scene_settings = "/srv/data/prog/scenes/scenes_settings.json"

def scene_path(src, lis_type, pdbid):
    return os.path.join(settings["DATADIR"], "wi-lists", src, "scenes",
                        lis_type, pdbid)

def scene_uptodate(src, lis_type, pdbid):
    if src.lower() == 'pdb':
        in_path = pdb_path(pdbid)
    elif src.lower() == 'redo':
        in_path = structurefactors_path(pdbid)
    else:
        raise Exception("no such structure type: %s" % src)
    dir_path = scene_path(src, lis_type, pdbid)
    sce_path = os.path.join(dir_path,
                            "%s_%s.sce" % (pdbid, lis_names[lis_type]))
    whynot_path = os.path.join(dir_path,
                               "%s_%s.whynot" % (pdbid, lis_names[lis_type]))

    for path in [sce_path, whynot_path]:
        if os.path.isfile(path) and (not os.path.isfile(in_path) or \
                os.path.getmtime(path) >= os.path.getmtime(in_path)):
            return True
    return False

def scene_obsolete(src, lis_type, pdbid):
    if src.lower() == 'pdb':
        in_path = pdb_path(pdbid)
    elif src.lower() == 'redo':
        in_path = final_path(pdbid)
    else:
        raise Exception("no such structure type: %s" % src)
    sce_path = os.path.join(
                  scene_path(src, lis_type, pdbid),
                  "%s_%s.sce" % (pdbid, lis_names[lis_type])
               )
    return os.path.isfile(sce_path) and not os.path.isfile(in_path)

def scene_remove(src, lis_type, pdbid):
    path = scene_path(src, lis_type, pdbid)
    if os.path.isdir(path):
        shutil.rmtree(path)

class SceneJob(Job):
    def __init__(self, src, lis_type, pdbid, wilist_job=None):
        if wilist_job is None:
            Job.__init__(self, "scene_%s_%s_%s" % (src, lis_type, pdbid), [])
        else:
            Job.__init__(self, "scene_%s_%s_%s" % (src, lis_type, pdbid), [wilist_job])
        self._src = src
        self._lis_type = lis_type
        self._pdbid = pdbid

    def run(self):
        if self._src.lower() == 'pdb':
            struct_path = pdb_path(self._pdbid)
        elif self._src.lower() == 'redo':
            struct_path = final_path(self._pdbid)
        else:
            raise Exception("unknown structure type %s" % self._src)

        in_path = wilist_data_path(self._src, self._lis_type, self._pdbid)
        root_dir = os.path.join(settings["DATADIR"],
                                "wi-lists/%s" % self._src)
        if os.path.isfile(in_path):
            os.environ["SCENES_SETTINGS"] = scene_settings
            log_command(_log, 'scene',
                        "%s %d %s %s %s %s %s" % (script, os.getpid(),
                                                  struct_path, self._pdbid,
                                                  self._src.upper(),
                                                  commands[self._lis_type],
                                                  in_path),
                        cwd=root_dir)

class SceneCleanupJob(Job):
    def __init__(self, fetch_job, src, lis_type):
        Job.__init__(self, "scene_clean_%s_%s" % (src, lis_type), [fetch_job])
        self._src = src
        self._lis_type = lis_type

    def run(self):
        for pdbid in os.listdir(os.path.join(settings["DATADIR"],
                                             "wi-lists", self._src,
                                             "scenes", self._lis_type)):
            if scene_obsolete(self._src, self._lis_type, pdbid):
                _log.warn("[scene] removing %s %s %s" % (self._src, self._lis_type, pdbid))
                scene_remove(self._src, self._lis_type, pdbid)
