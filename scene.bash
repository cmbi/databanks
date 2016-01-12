#!/bin/bash

export SCENES_SETTINGS=/data/prog/scenes/scenes_settings.json

whynotdir=/data/scratch/whynot2

if [ $# -ne 3 ] ; then 
	exit 1
fi

inputtype=$1
lis=$2
pdbid=$3

title=$lis
command=$lis
if [ $lis == 'ss2' ] ; then title=sym-contacts ; command=symm
elif [ $lis == 'iod' ] ; then title=ion-sites ; command=ion
fi


if [ $inputtype == 'pdb' ] ; then structure=/data/pdb/flat/pdb$pdbid.ent
elif [ $inputtype == 'redo' ] ;	then structure=/data/pdb_redo/`echo $pdbid | cut -c2-3`/$pdbid/$pdbid'_final.pdb'
fi
listfile=/data/wi-lists/$inputtype/$lis/$pdbid/$pdbid.$lis.bz2

dir=/data/wi-lists/$inputtype/scenes/$lis/$pdbid
if ! [ -d $dir ] ; then
	mkdir -p $dir
fi

cd $dir

outputfile=$dir/$pdbid'_'$title.sce
whynotfile=$dir/$pdbid'_'$title.whynot
prevwhynotfile="/data/status/scenes-$inputtype-$lis-$pdbid.prevwhynot"
[ -f $whynotfile ] && mv $whynotfile $prevwhynotfile

# redirect yasara output to /dev/null, otherwise the log gets too full!

uppercasetype=`echo $inputtype | tr [a-z] [A-Z]`

/usr/local/bin/scenes $$ $structure $pdbid $uppercasetype $command $listfile > /dev/null

[ -f $whynotfile.check ] && cp $whynotfile.check $whynotfile

/data/bin/whynot-update.bash $prevwhynotfile $whynotfile $outputfile scenes-$inputtype-$lis
