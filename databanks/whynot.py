import os
from sets import Set
from urllib2 import urlopen, HTTPError

from databanks.settings import settings
from databanks.queue import Job
from databanks.command import log_command

import logging
_log = logging.getLogger(__name__)

CRAWL = '/srv/data/scratch/whynot2/crawl.py'
ANNOTATE = '/srv/data/scratch/whynot2/annotate.py'
URL = 'http://www.cmbi.ru.nl/WHY_NOT2'

class WhynotCrawlJob(Job):
    def __init__(self, databank, path, data_jobs):
        Job.__init__(self, "whynot_%s" % databank, data_jobs)
        self._databank = databank
        self._path = path

    def run(self):
        log_command(_log, 'whynot', "%s %s %s" % (CRAWL, self._databank, self._path))


def annotated_set(databank):
    try:
        return Set(urlopen(URL + '/resources/list/%s_ANNOTATED' % databank).read().split())
    except HTTPError:
        return Set()
