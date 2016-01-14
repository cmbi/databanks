#!/bin/bash

GetConfVar ()
{
    sed -n "s/^$1\\s*=\\s*\\(.*\\)/\1/p" databanks.conf
}

DATADIR=`GetConfVar DATADIR`

id=$1
divid=$(echo $id | cut -c2-3)

bdbdirpath=$DATADIR'bdb'/$divid/$id
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
