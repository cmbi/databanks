#!/bin/bash

id=$1
divid=$(echo $id | cut -c2-3)

whynotdir=/srv/data/scratch/whynot2
CCP4SETUP=/srv/data/bin/ccp4-7.0/bin/ccp4.setup-sh
#CCP4SETUP=/srv/data/zata/ccp4-7.0/setup-scripts/ccp4.setup-sh

bdbdirpath=/srv/data/bdb/$divid/$id
bdbfilepath=$bdbdirpath/$id.bdb

whynotfile="$bdbdirpath/$id.whynot"
prevwhynotfile="/data/status/bdb-$id.prevwhynot"
if [ -f $whynotfile ] ; then
	mv $whynotfile $prevwhynotfile
fi

rm -f $bdbdirpath/*

# Run the BDB script:

bash -c "source $CCP4SETUP; /usr/local/bin/mkbdb /srv/data/bdb/ /srv/data/pdb/flat/pdb$id.ent $id" 

/srv/data/bin/whynot-update.bash $prevwhynotfile $whynotfile $bdbfilepath bdb

chmod 755 $bdbdirpath $(dirname $bdbdirpath)
chmod 644 $bdbfilepath
