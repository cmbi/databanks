#!/bin/bash

whatif=/srv/data/prog/wi-lists/whatif/src/whatif

filepath=$1
filename=`basename $filepath`
pdbid=`basename $filepath | sed -e 's/\(pdb\)\?\(....\)\(_.*\)\?\..*/\2/'`

workdir=/srv/data/tmp/wif-$$

log=$pdbid.hb2.log

mkdir $workdir
cd $workdir

/usr/bin/timeout 20s $whatif > /dev/null 2> $pdbid.err << WHATIF_CMD
GETMOL $filename Y $pdbid
HBONDS
HB2INI

DOLOG $log 0
HBONDS
HB2LIS protein 0 protein 0
NOLOG
FULLST Y
WHATIF_CMD

if ! [ -f $log ] ; then

    exit 1
fi

tail -n +2 $log | sed -e 's/->/-/'
#tail -n +2 $log | cut -c1-61 | sed -e 's/->/-/'

cd ..
rm -rf $workdir
