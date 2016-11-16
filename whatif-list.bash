#!/bin/bash

whynotdir=/srv/data/scratch/whynot2

if [ $# -ne 3 ] ; then 
	exit 1
fi

inputtype=$1
listype=$2
pdbid=$3

flag=
if [ $inputtype == 'redo' ] ; then
	flag='setwif 498 2'
fi

dir=/srv/data/wi-lists/$inputtype/$listype/$pdbid
if ! [ -d $dir ] ; then
	mkdir -p $dir
fi

cd $dir

outputfile=$dir/$pdbid.$listype.bz2
whynotfile=$dir/$pdbid.$listype.whynot
prevwhynotfile="/srv/data/status/wi-$inputtype-$listype-$pdbid.prevwhynot"
if [ -f $whynotfile ] ; then
    mv $whynotfile $prevwhynotfile
fi

if ! [ -f /srv/data/pdb_redo/flat/$pdbid'_final_tot.pdb' ] &&
     [ -f /srv/data/pdb_redo/${pdbid:1:2}/$pdbid/$pdbid'_final_tot.pdb' ] ;
    then
        /bin/ln -s /srv/data/pdb_redo/${pdbid:1:2}/$pdbid/$pdbid'_final_tot.pdb' /srv/data/pdb_redo/flat/$pdbid'_final_tot.pdb'
fi

# redirect whatif output to file, otherwise the update log gets too full!

whatiflog=whatif$$.log
/usr/bin/timeout 20s /srv/data/prog/wi-lists/whatif/src/whatif $flag lists lis$listype $pdbid Y fullst Y > $whatiflog

if [ -f $dir/$pdbid.$listype ] ; then
    # happens sometimes
    /bin/bzip2  $dir/$pdbid.$listype
fi

if ! [ -f $whynotfile ] && ! [ -f $outputfile ] ; then

    /bin/cat $whatiflog
fi
rm $whatiflog

# Remove whatif runtime files:
# (remove everything but the list or whynot file)
rm -f `find $dir -mindepth 1 | grep -v $pdbid.$listype`

/srv/data/bin/whynot-update.bash $prevwhynotfile $whynotfile $outputfile wi-list-$inputtype-$listype
