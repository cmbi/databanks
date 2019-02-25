import sys
import os

import logging
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

root_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(root_path)
from databanks.pdbfinder2 import Pdbfinder2DatJob, Pdbfinder2JoinJob

if len(sys.argv) == 1:
    Pdbfinder2JoinJob().run()
elif len(sys.argv) > 1:
    for pdbid in sys.argv[1:]:
        Pdbfinder2DatJob(pdbid).run()
else:
    print "Usage: %s pdbid" % sys.argv[0]
    print "Usage: %s" % sys.argv[0]
