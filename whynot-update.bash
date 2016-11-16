#!/bin/bash

whynotdir=/srv/data/scratch/whynot2

if [ $# -ne 4 ] ; then
    exit 1
fi

prevwhynotfile=$1
whynotfile=$2
outputfile=$3
annotationname=$4

# Annotate whynot output
if [ -f $whynotfile ] ; then

	# Don't use empty whynot files
	if ! [ "$(cat $whynotfile)" ] ; then

		echo $whynotfile is empty

	# If the whynot file is new, it must be annotated.

	elif ! [ -f $prevwhynotfile ] || ! diff -q $whynotfile $prevwhynotfile ; then

		cat $whynotfile | sed 's|\s\+(\s*[\*0-9]\+\s*)\s*$||g' >> $whynotdir/comment/$annotationname"_$(date +%Y%m%d).txt"
	fi

elif ! [ -f $outputfile ] ; then

	if [ -f $prevwhynotfile ] ; then mv $prevwhynotfile $whynotfile ; fi

	echo missing both $outputfile and $whynotfile
	exit 1
fi

if [ -f $prevwhynotfile ] && (! [ -f $whynotfile ] || ! diff -q $whynotfile $prevwhynotfile ) ; then

	# Whynot files that are no longer valid must be uncommented.
	cat $prevwhynotfile >> $whynotdir/uncomment/$annotationname"_$(date +%Y%m%d).txt"
fi

rm -f $prevwhynotfile
