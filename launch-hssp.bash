#!/bin/bash

MAXNJOB=32

GetConfVar ()
{
    sed -n "s/^$1\\s*=\\s*\\(.*\\)/\1/p" databanks.conf
}

TMPDIR=`GetConfVar TMPDIR`
DATADIR=`GetConfVar DATADIR`
MKHSSP=`GetConfVar MKHSSP`
CVHSSP=`GetConfVar CVHSSP`
NICE=`GetConfVar NICE`

# Tells whether the given hssp file is being created at the moment.
function mkhsspRunning {

	ps -efww | grep mkhssp | grep -qE "\-o\s*/.*/$1.hssp.bz2"
}

# Gives the number of active mkhssp, whatif, pdb_redo and whatcheck processes.
countJOBS () {

	expr `ps -e | grep -cE 'mkhssp$'` + `ps -e | grep -cE 'whatif$'` + `ps -e | grep -cE 'pdb_redo'` + `ps -e | grep -cE 'whatcheck$'`
}

DATABANKS="-d /data/fasta/uniprot_sprot.fasta -d /data/fasta/uniprot_trembl.fasta"

while true ; do

    # Remake the oldest hssp files..
	for file in `ls -tr $DATADIR'hssp3'/` ; do

        # Stop adding if the maximum number of jobs is running.
		if [ `countJOBS` -ge $MAXNJOB ] ; then sleep 300 ; break ; fi

		pdbid=${file%.hssp.bz2}
		if ! mkhsspRunning $pdbid ; then

            structfile=$DATADIR'pdb'/all/pdb$pdbid.ent.gz
            if ! [ -f $structfile ] ; then

                structfile=$DATADIR'mmCIF'/$pdbid.cif.gz
            fi

            tmpfile=$TMPDIR$file

            # Run in background..
			( $NICE -n 19 $MKHSSP -o $tmpfile -a 1 -m 2500 --fetch-dbrefs $structfile $DATABANKS && \
                    mv $tmpfile $DATADIR'hssp3'/$file && $CVHSSP $DATADIR'hssp3'/$file $DATADIR'hssp'/$file ) &

			sleep 10
		fi
	done
done

# Wait for the jobs to finish..
wait
