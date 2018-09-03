import sys
import os
from time import strftime, gmtime

root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(root_dir)

from databanks.pdbredo import pdbredo_uptodate, pdbredo_obsolete, final_path
from databanks.structurefactors import structurefactors_path
from databanks.mmcif import mmcif_path
from databanks.pdb import pdb_path, pdb_flat_path
from databanks.hssp import hssp_uptodate, hssp_obsolete, hssp1_path, hssp3_path
from databanks.bdb import bdb_uptodate, bdb_obsolete, bdb_path
from databanks.wilist import (lis_types, wilist_path, wilist_data_path,
                              wilist_uptodate, wilist_obsolete)

def yesno(boolean):
    if boolean:
        return "yes"
    else:
        return "no"

def s_mtime(path):
    return strftime("%Y %B %d, %H:%M:%S", gmtime(os.path.getmtime(path)))

if len(sys.argv) == 2:
    pdbid = sys.argv[1]

    print "mmcif:"
    path = mmcif_path(pdbid)
    print "\tpath:", path
    if os.path.isfile(path):
        print "\tmodification time:", s_mtime(path)
    else:
        print "\t<absent>"

    print "pdb:"
    for path in [pdb_path(pdbid), pdb_flat_path(pdbid)]:
        print "\tpath:", path
        if os.path.isfile(path):
            print "\tmodification time:", s_mtime(path)
        else:
            print "\t<absent>"

    print "bdb:"
    path = bdb_path(pdbid)
    print "\tpath:", path
    if os.path.isdir(path):
        print "\tmodification time:", s_mtime(path)
        print "\tup to date:", yesno(bdb_uptodate(pdbid))
        print "\tobsolete:", yesno(bdb_obsolete(pdbid))
    else:
        print "\t<absent>"

    print "hssp:"
    path = hssp3_path(pdbid)
    print "\tpath:", path
    if os.path.isfile(path):
        print "\tmodification time:", s_mtime(path)
    else:
        print "\t<absent>"
    path = hssp1_path(pdbid)
    print "\tpath:", path
    if os.path.isfile(path):
        print "\tmodification time:", s_mtime(path)
        print "\tup to date:", yesno(hssp_uptodate(pdbid))
        print "\tobsolete:", yesno(hssp_obsolete(pdbid))
    else:
        print "\t<absent>"

    print "structure factors:"
    path = structurefactors_path(pdbid)
    print "\tpath:", path
    if os.path.isfile(path):
        print "\tmodification time:", s_mtime(path)
    else:
        print "\t<absent>"

    print "pdbredo:"
    path = final_path(pdbid)
    print "\tpath:", path
    if os.path.isfile(path):
        print "\tmodification time:", s_mtime(final_path(pdbid))
        print "\tup to date:", yesno(pdbredo_uptodate(pdbid))
        print "\tobsolete:", yesno(pdbredo_obsolete(pdbid))
    else:
        print "\t<absent>"

    for src in ['pdb', 'redo']:
        for lis_type in lis_types:
            print src, lis_type + ':'
            path = wilist_data_path(src, lis_type, pdbid)
            print "\tpath:", path
            if os.path.isfile(path):
                print "\tmodification time:", s_mtime(path)
                print "\tup to date:", yesno(wilist_uptodate(src, lis_type, pdbid))
                print "\tobsolete:", yesno(wilist_obsolete(src, lis_type, pdbid))
            else:
                print "\t<absent>"

else:
    print "Usage: %s pdbid" % sys.argv[0]
