import os
import sys

import logging
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

root_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(root_path)

from databanks.fetch import FetchPdbredoJob

if len(sys.argv) == 1:
    FetchPdbredoJob().run()
else:
    print "Usage: %s" % sys.argv[0]
