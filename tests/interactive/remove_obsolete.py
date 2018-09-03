import sys
import os
from argparse import ArgumentParser

import logging
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

root_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(root_path)

from databanks.bdb import BdbCleanupJob
from databanks.dssp import DsspCleanupJob
from databanks.hssp import HsspCleanupJob

parser = ArgumentParser(description="remove obsolete entries")
parser.add_argument("databank", choices=['bdb', 'dssp', 'hssp'])
args = parser.parse_args()

if args.databank == 'bdb':
    BdbCleanupJob().run()
elif args.databank == 'dssp':
    DsspCleanupJob().run()
elif args.databank == 'hssp':
    HsspCleanupJob().run()
