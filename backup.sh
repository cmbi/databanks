#!/bin/sh

USER=probio

LOGFILE=/srv/data/status/backup.mirror_log

MAILADDRESS=cbaakman@cmbi.ru.nl

sudo -u $USER /usr/bin/rsync \
            -rltvC --no-p --chmod=ugo=rwX --exclude=".svn" --exclude="status" --exclude="scratch/www"  --exclude="mongodb"\
            --exclude="enzyme" --exclude="flags" --exclude="pdb_seqres.txt" --exclude="yasara/" --exclude="whatif/"\
            --exclude="structure_factors" --exclude="pdb" --exclude="XML-noatom" --exclude="zata" --exclude="whatcheck"\
            --exclude="mmCIF" --exclude="rcsb" --exclude="pdbechem" --exclude="flags" --exclude="gpcr-models"\
            --exclude="mrs" --exclude="uniprot" --exclude="blast" --exclude="fasta" --exclude="tmp" --exclude="tupload" \
            --exclude="embl" --exclude="genbank" --exclude="gene" --exclude="omim" --exclude="oxford" --exclude="mimmap" --include="*" \
        /srv/data/ /research/chelonium/data/ > $LOGFILE 2>&1

sudo -u $USER /usr/bin/rsync -av /lib/systemd/system/ /research/system/ >> $LOGFILE 2>&1

if [ "$?" != 0 ] ; then

    echo Backup failed >> $LOGFILE
    cat $LOGFILE | mail -s chelonium-backup $MAILADDRESS
    exit $?
fi

echo Backup done >> $LOGFILE

cat $LOGFILE | mail -s chelonium-backup $MAILADDRESS
