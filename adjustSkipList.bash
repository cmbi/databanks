#!/bin/bash

GetConfVar ()
{
    sed -n "s/^$1\\s*=\\s*\\(.*\\)/\1/p" databanks.conf
}

TMPDIR=`GetConfVar TMPDIR`
DATADIR=`GetConfVar DATADIR`

if [ $# -ne 1 ] ; then exit 1 ; fi

listfile=$1
tempfile=$TMPDIR$(basename $listfile)

cp $listfile $tempfile

for id in $(cat $listfile) ; do
	if test $DATADIR'pdb'/all/pdb$id.ent.gz -nt $listfile ; then
		grep -v $id $tempfile > $tempfile
	fi 
done

touch -r $listfile $tempfile
cp -p $tempfile $listfile
rm $tempfile
