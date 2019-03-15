import os
import sys

import logging
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

root_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(root_path)

from databanks.fetch import FetchPdbJob
from databanks.pdb import PdbCleanupJob, PdbExtractJob, pdb_path

if len(sys.argv) == 1:
    fetch_job = FetchPdbJob()
    fetch_job.run()
    PdbCleanupJob(fetch_job).run()
elif len(sys.argv) == 2:
    PdbExtractJob(pdb_path(sys.argv[1])).run()
else:
    print("Usage: %s pdbid" % sys.argv[0])
    print("Usage: %s" % sys.argv[0])
