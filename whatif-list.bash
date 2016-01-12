#!/bin/bash

whynotdir=/data/scratch/whynot2

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

dir=/data/wi-lists/$inputtype/$listype/$pdbid
if ! [ -d $dir ] ; then
	mkdir -p $dir
fi

cd $dir

outputfile=$dir/$pdbid.$listype.bz2
whynotfile=$dir/$pdbid.$listype.whynot
prevwhynotfile="/data/status/wi-$inputtype-$listype-$pdbid.prevwhynot"
if [ -f $whynotfile ] ; then
    mv $whynotfile $prevwhynotfile
fi

# redirect whatif output to /dev/null, otherwise the log gets too full!

/usr/bin/timeout 20s /data/prog/wi-lists/whatif/src/whatif $flag lists lis$listype $pdbid Y fullst Y > /dev/null

if [ -f $dir/$pdbid.$listype ] ; then
    # happens sometimes
    /bin/bzip2  $dir/$pdbid.$listype
fi

# Remove whatif runtime files:
# (remove everything but the list or whynot file)
rm -f `find $dir -mindepth 1 | grep -v $pdbid.$listype`

/data/bin/whynot-update.bash $prevwhynotfile $whynotfile $outputfile wi-list-$inputtype-$listype
