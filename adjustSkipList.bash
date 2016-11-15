#!/bin/bash

if [ $# -ne 1 ] ; then exit 1 ; fi

listfile=$1
tempfile=/tmp/$(basename $listfile)

cp $listfile $tempfile

for id in $(cat $listfile) ; do
	if test /data/pdb/all/pdb$id.ent.gz -nt $listfile ; then
		grep -v $id $tempfile > $tempfile
	fi 
done

touch -r $listfile $tempfile
cp -p $tempfile $listfile
rm $tempfile
