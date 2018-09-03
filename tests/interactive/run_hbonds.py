import sys
import os
from argparse import ArgumentParser

import logging
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

root_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(root_path)
from databanks.hbonds import HbondsJob

parser = ArgumentParser(description="run a whatif hydrogen bonds job")
parser.add_argument("pdbid", help="four character code, identifying the pdb entry")
args = parser.parse_args()

HbondsJob(args.pdbid).run()
