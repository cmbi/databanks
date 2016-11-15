#!/bin/bash

MAXNJOB=32

function mkhsspRunning {

    ps -efww | grep mkhssp | grep -qE "\-o\s*/.*/$1.hssp.bz2"
}

countJOBS () {

    expr `ps -e | grep -cE 'mkhssp$'` + `ps -e | grep -cE 'whatif$'` + `ps -e | grep -cE 'pdb_redo'` + `ps -e | grep -cE 'whatcheck$'`
}

DATABANKS="-d /data/fasta/uniprot_sprot.fasta -d /data/fasta/uniprot_trembl.fasta"

while true ; do

    for file in `ls -tr /data/hssp3/` ; do

        if [ `countJOBS` -ge $MAXNJOB ] ; then sleep 300 ; break ; fi

        pdbid=${file%.hssp.bz2}
        if ! mkhsspRunning $pdbid ; then

            ( /usr/bin/nice -n 19 /usr/local/bin/mkhssp -o /data/tmp/$file -a 1 -m 2500 --fetch-dbrefs /data/pdb/all/pdb$pdbid.ent.gz $DATABANKS && mv /data/tmp/$file /data/hssp3/$file && /usr/local/bin/hsspconv /data/hssp3/$file /data/hssp/$file ) &

            sleep 10
        fi
    done
done

wait
