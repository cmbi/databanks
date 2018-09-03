import sys
import os
from argparse import ArgumentParser

import logging
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

root_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(root_path)
from databanks.scene import SceneJob, lis_types

parser = ArgumentParser(description="run a wi list scene job")
parser.add_argument("source", choices=['pdb', 'redo'], help="source of the structure data")
parser.add_argument("listype", choices=lis_types, help="type of data generated")
parser.add_argument("pdbid", help="four character code, identifying the pdb entry")
args = parser.parse_args()

SceneJob(args.source, args.listype, args.pdbid).run()
