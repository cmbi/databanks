import sys
import os
from argparse import ArgumentParser

import logging
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

root_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(root_path)
from databanks.bdb import BdbJob

parser = ArgumentParser(description="run a bdb job for a single pdb entry")
parser.add_argument("pdbid", help="four character code, identifying the pdb entry")
args = parser.parse_args()

BdbJob(args.pdbid).run()
