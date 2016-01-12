#!/bin/bash

id=$1
divid=$(echo $id | cut -c2-3)

whynotdir=/data/scratch/whynot2

bdbdirpath=/data/bdb/$divid/$id
bdbfilepath=$bdbdirpath/$id.bdb

whynotfile="$bdbdirpath/$id.whynot"
prevwhynotfile="/data/status/bdb-$id.prevwhynot"
if [ -f $whynotfile ] ; then
	mv $whynotfile $prevwhynotfile
fi

rm -f $bdbdirpath/*

# Run the BDB script:

bash -c "source /srv/zata/ccp4-6.5/bin/ccp4.setup-sh; /usr/local/bin/mkbdb /data/bdb/ /data/pdb/flat/pdb$id.ent $id" 

/data/bin/whynot-update.bash $prevwhynotfile $whynotfile $bdbfilepath bdb
