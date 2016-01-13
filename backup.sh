#!/bin/sh

GetConfVar ()
{
    sed -n "s/^$1\\s*=\\s*\\(.*\\)/\1/p" databanks.conf
}

STATSDIR=`GetConfVar STATSDIR`
DATADIR=`GetConfVar DATADIR`

sudo -u probio /usr/bin/rsync \
        -rltvC --no-p --chmod=ugo=rwX --exclude=".svn" --exclude="status" --exclude="scratch/www"  --exclude="mongodb" \
            --exclude="enzyme" --exclude="flags" --exclude="pdb_seqres.txt" --exclude="yasara/" --exclude="whatif/" \
            --exclude="structure_factors" --exclude="pdb" --exclude="XML-noatom" --exclude="zata" --exclude="whatcheck" \
            --exclude="mmCIF" --exclude="rcsb" --exclude="pdbechem" --exclude="flags" --exclude="gpcr-models" \
            --exclude="mrs" --exclude="uniprot" --exclude="blast" --exclude="fasta" --exclude="tmp" --include="*" \
        $DATADIR /research/cmbi4/data/ 1> $STATSDIR'backup.mirror_log' 2>&1 \
            || (echo backup >> $STATSDIR'failed_dbs.txt' ; exit 1)

echo Backup done ;
/usr/bin/touch $STATSDIR'backup.mirror_done'
