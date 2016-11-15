#!/bin/sh

sudo -u probio /usr/bin/rsync \
            -rltvC --no-p --chmod=ugo=rwX --exclude=".svn" --exclude="status" --exclude="scratch/www"  --exclude="mongodb"\
            --exclude="enzyme" --exclude="flags" --exclude="pdb_seqres.txt" --exclude="yasara/" --exclude="whatif/"\
            --exclude="structure_factors" --exclude="pdb" --exclude="XML-noatom" --exclude="zata" --exclude="whatcheck"\
            --exclude="mmCIF" --exclude="rcsb" --exclude="pdbechem" --exclude="flags" --exclude="gpcr-models"\
            --exclude="mrs" --exclude="uniprot" --exclude="blast" --exclude="fasta" --exclude="tmp" --exclude="tupload" --include="*" \
        /srv/data/ /research/chelonium/data/ > /srv/data/status/backup.mirror_log 2>&1

if [ "$?" != 0 ] ; then

    echo Backup failed >> /srv/data/status/backup.mirror_log
    echo backup >> /srv/data/status/failed_dbs.txt
    exit $?
fi

echo Backup done >> /srv/data/status/backup.mirror_log
/usr/bin/touch /srv/data/status/backup.mirror_done

cat /srv/data/status/backup.mirror_log | mail -s cmbi4-backup cbaakman@cmbi.ru.nl
