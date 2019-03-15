import os
import sys

from argparse import ArgumentParser

root_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(root_path)

from hssp_rotate import count_hits
from databanks.hssp import hssp3_path

parser = ArgumentParser(description="count the number of hits in a hssp file")
parser.add_argument("pdbid", help="four letter code of pdb entry")
args = parser.parse_args()

print(count_hits(hssp3_path(args.pdbid)))
