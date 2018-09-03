import sys
import os
from argparse import ArgumentParser

import logging
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

root_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(root_path)
from databanks.hssp import HgHsspJob

parser = ArgumentParser(description="run a hssp job")
parser.add_argument("seqid", help="hash code, identifying the sequence")
args = parser.parse_args()

HgHsspJob(args.seqid).run()
