import sys
import os

import logging
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

root_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(root_path)
from databanks.pdbfinder import PdbfinderDatJob, PdbfinderJoinJob

if len(sys.argv) == 1:
    PdbfinderJoinJob().run()
elif len(sys.argv) == 2:
    PdbfinderDatJob(sys.argv[1]).run()
else:
    print "Usage: %s pdbid" % sys.argv[0]
    print "Usage: %s" % sys.argv[0]
