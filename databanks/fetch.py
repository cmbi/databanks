import os
from gzip import GzipFile

from databanks.queue import Job
from databanks.data import list_pdbgz, list_mmcif, list_pdbredo
from databanks.settings import settings
from databanks.command import log_command
from ftplib import FTP
from urllib.request import urlopen

import logging
_log = logging.getLogger(__name__)


class FetchPdbJob(Job):
    def __init__(self):
        Job.__init__(self, "fetch_pdb")

    def run(self):
        excludes = ''
        for pdbid in settings["FRAUD_IDS"]:
            excludes += " --exclude=\'pdb%s.ent.gz\'" % pdbid

        log_command(_log, 'pdb',
            "/usr/bin/rsync -rtv --delete --port=33444" +
            " --include=\'pdb????.ent.gz\' --exclude=\'*\'" + excludes +
            " rsync.wwpdb.org::ftp_data/structures/divided/pdb/**/" +
            " %s" % os.path.join(settings["DATADIR"], 'pdb/all/'),
            timeout=24*60*60
        )

class FetchPdbredoJob(Job):
    def __init__(self):
        Job.__init__(self, "fetch_pdbredo")

    def run(self):
        excludes = ''
        for pdbid in settings["FRAUD_IDS"]:
            excludes += " --exclude=\'%s\'" % pdbid

        log_command(_log, 'pdbredo',
            "/usr/bin/rsync -av --delete" +
            " rsync://rsync.pdb-redo.eu/pdb-redo/" +
            " %s" % os.path.join(settings["DATADIR"], 'pdb_redo/'),
            timeout=24*60*60
        )

class FetchMmcifJob(Job):
    def __init__(self):
        Job.__init__(self, "fetch_mmcif")

    def run(self):
        excludes = ''
        for pdbid in settings["FRAUD_IDS"]:
            excludes += " --exclude=\'%s.cif.gz\'" % pdbid

        log_command(_log, 'mmcif',
            "/usr/bin/rsync -rtv --delete --port=33444" +
            " --include=\'????.cif.gz\' --exclude=\'*\'" + excludes +
            " rsync.wwpdb.org::ftp_data/structures/divided/mmCIF/**/" +
            " %s" % os.path.join(settings["DATADIR"], 'mmCIF/'),
            timeout=24*60*60
        )

class FetchNmrJob(Job):
    def __init__(self):
        Job.__init__(self, "fetch_nmr")

    def run(self):
        excludes = ''
        for pdbid in settings["FRAUD_IDS"]:
            excludes += " --exclude=\'%s.mr.gz\'" % pdbid

        log_command(_log, 'nmr',
            "/usr/bin/rsync -rtv --delete --port=33444" +
            " --include=\'????.mr.gz\' --exclude=\'*\'" + excludes +
            " rsync.wwpdb.org::ftp_data/structures/divided/nmr_restraints/**/" +
            " %s" % os.path.join(settings["DATADIR"], 'nmr_restraints/'),
            timeout=24*60*60
        )

class FetchStructureFactorsJob(Job):
    def __init__(self):
        Job.__init__(self, "fetch_sf")
    def run(self):
        excludes = ''
        for pdbid in settings["FRAUD_IDS"]:
            excludes += " --exclude=\'r%ssf.ent.gz\'" % pdbid

        log_command(_log, 'structure_factors',
            "/usr/bin/rsync -rtv --delete --port=33444" +
            " --include=\'r????sf.ent.gz\' --exclude=\'*\'" + excludes +
            " rsync.wwpdb.org::ftp_data/structures/divided/structure_factors/**/" +
            " %s" % os.path.join(settings["DATADIR"], 'structure_factors/'),
            timeout=24*60*60
        )

class FetchGenbankJob(Job):
    def __init__(self):
        Job.__init__(self, "fetch_genbank")

    def run(self):
        log_command(_log, 'genbank',
            "/usr/bin/rsync -rtv --delete" +
            " --include=\'*.seq.gz\' --exclude=\'*\'" +
            " rsync://ftp.ncbi.nih.gov/genbank/" +
            " %s" % os.path.join(settings["DATADIR"], 'genbank/'),
            timeout=24*60*60
        )

class FetchGeneJob(Job):
    def __init__(self):
        Job.__init__(self, "fetch_gene")

    def run(self):
        log_command(_log, 'gene',
            "/usr/bin/rsync" +
            " rsync://ftp.ncbi.nlm.nih.gov/gene/DATA/ASN_BINARY/All_Data.ags.gz" +
            " %s" % os.path.join(settings["DATADIR"], 'gene/'),
            timeout=24*60*60
        )

class FetchGoJob(Job):
    def __init__(self):
        Job.__init__(self, "fetch_go")

    def run(self):
        with FTP('ftp.geneontology.org') as ftp:
            ftp.login()
            ftp.cwd('pub/go/ontology/')
            destdir = os.path.join(settings["DATADIR"], 'go')
            if not os.path.isdir(destdir):
                os.mkdir(destdir)
            with open(os.path.join(destdir, 'gene_ontology.obo'), 'wb') as f:
                _log.info("[go] retrieve gene_ontology.obo")
                ftp.retrbinary('RETR gene_ontology.obo', f.write)

class FetchEmblJob(Job):
    def __init__(self):
        Job.__init__(self, "fetch_embl")

    def run(self):
        with FTP('ftp.ebi.ac.uk') as ftp:
            ftp.login()
            ftp.cwd('pub/databases/ena/sequence/release/')
            destdir = os.path.join(settings["DATADIR"], 'embl')
            if not os.path.isdir(destdir):
                os.mkdir(destdir)
            for dirname in ftp.nlst():
                for filename in ftp.nlst(dirname):
                    filename = os.path.basename(filename)
                    if filename.endswith('.dat.gz'):
                        rpath = os.path.join(dirname, filename)
                        dpath = os.path.join(destdir, dirname)
                        if not os.path.isdir(dpath):
                            os.mkdir(dpath)
                        path = os.path.join(destdir, rpath)
                        with open(path, 'wb') as f:
                            _log.info("[embl] retrieve %s" % rpath)
                            ftp.retrbinary('RETR %s' % rpath, f.write)

class FetchUniprotJob(Job):
    def __init__(self):
        Job.__init__(self, "fetch_uniprot")

    def run(self):
        uniprot_dir = os.path.join(settings["DATADIR"], 'uniprot/')
        fasta_dir = os.path.join(settings["DATADIR"], 'fasta/')

        if not os.path.isdir(uniprot_dir):
            os.mkdir(uniprot_dir)

        for filename in ['uniprot_sprot.fasta.gz', 'uniprot_trembl.fasta.gz',
                         'uniprot_sprot.dat.gz', 'uniprot_trembl.dat.gz',
                         'README', 'reldate.txt']:
            log_command(_log, 'uniprot',
                '/usr/bin/wget' +
                ' ftp://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/complete/%s' % filename +
                ' -N -P %s' % uniprot_dir,
                timeout=24*60*60
            )

        #ftp = FTP('ftp.uniprot.org', timeout=3600)
        #ftp.login()
        #ftp.cwd('pub/databases/uniprot/current_release/knowledgebase/complete/')
        #for filename in ['uniprot_sprot.fasta.gz', 'uniprot_trembl.fasta.gz',
        #                 'uniprot_sprot.dat.gz', 'uniprot_trembl.dat.gz',
        #                 'README', 'reldate.txt']:
        #    with open(os.path.join(uniprot_dir, filename), 'wb') as f:
        #        _log.info("[uniprot] retrieve %s" % filename)
        #        ftp.retrbinary('RETR %s' % filename, f.write)
        #ftp.quit()

        # Decompress fastas:
        for filename in ['uniprot_sprot.fasta.gz', 'uniprot_trembl.fasta.gz']:
            fastaname = os.path.splitext(filename)[0]
            fasta_path = os.path.join(fasta_dir, fastaname)
            _log.info("[uniprot] extract to %s" % fasta_path)
            with open(fasta_path, 'wb') as f:
                with GzipFile(os.path.join(uniprot_dir, filename), 'rb') as g:
                    while True:
                        chunk = g.read(65536)
                        if len(chunk) <= 0:
                            break
                        f.write(chunk)

class FetchInterproJob(Job):
    def __init__(self):
        Job.__init__(self, "fetch_interpro")

    def run(self):
        with FTP('ftp.ebi.ac.uk') as ftp:
            ftp.login()
            ftp.cwd('pub/databases/interpro/current/')
            destdir = os.path.join(settings["DATADIR"], 'interpro')
            if not os.path.isdir(destdir):
                os.mkdir(destdir)
            with open(os.path.join(destdir, 'interpro.xml.gz'), 'wb') as f:
                _log.info("[interpro] retrieve interpro.xml.gz")
                ftp.retrbinary('RETR interpro.xml.gz', f.write)

class FetchMimmapJob(Job):
    def __init__(self):
        Job.__init__(self, "fetch_mimmap")

    def run(self):
        with FTP('ftp.ncbi.nih.gov') as ftp:
            ftp.login()
            ftp.cwd('repository/OMIM/ARCHIVE')
            destdir = os.path.join(settings["DATADIR"], 'mimmap')
            if not os.path.isdir(destdir):
                os.mkdir(destdir)
            with open(os.path.join(destdir, 'genemap'), 'wb') as f:
                _log.info("[mimmap] retrieve genemap")
                ftp.retrbinary('RETR genemap', f.write)

class FetchOmimJob(Job):
    def __init__(self):
        Job.__init__(self, "fetch_omim")

    def run(self):
        with FTP('ftp.ncbi.nih.gov') as ftp:
            ftp.login()
            ftp.cwd('repository/OMIM/ARCHIVE')
            destdir = os.path.join(settings["DATADIR"], 'omim')
            if not os.path.isdir(destdir):
                os.mkdir(destdir)
            with open(os.path.join(destdir, 'omim.txt.Z'), 'wb') as f:
                _log.info("[omim] retrieve omim.txt.Z")
                ftp.retrbinary('RETR omim.txt.Z', f.write)

class FetchOxfordJob(Job):
    def __init__(self):
        Job.__init__(self, "fetch_oxford")

    def run(self):
        with FTP('ftp.informatics.jax.org') as ftp:
            ftp.login()
            ftp.cwd('pub/reports')
            destdir = os.path.join(settings["DATADIR"], 'oxford')
            if not os.path.isdir(destdir):
                os.mkdir(destdir)
            with open(os.path.join(destdir,'HMD_HumanPhenotype.rpt'), 'wb') as f:
                _log.info("[oxford] retrieve HMD_HumanPhenotype.rpt")
                ftp.retrbinary('RETR HMD_HumanPhenotype.rpt', f.write)

class FetchPfamJob(Job):
    def __init__(self):
        Job.__init__(self, "fetch_pfam")

    def run(self):
        log_command(_log, 'pfam',
            "/usr/bin/rsync -rtv --delete --include=\'Pfam-A.full.gz\'" +
            " --include='Pfam-A.seed.gz' --exclude=\'*\'" +
            " rsync://ftp.ebi.ac.uk/pub/databases/Pfam/current_release/"
            " %s" % os.path.join(settings["DATADIR"], 'pfam/'),
            timeout=24*60*60
        )

class FetchPmcJob(Job):
    def __init__(self):
        Job.__init__(self, "fetch_pmc")

    def run(self):
        log_command(_log, 'pmc',
            "/usr/bin/rsync -rtv --delete" +
            " --include=\'articles*.tar.gz\' --exclude=\'*\'" +
            " rsync://ftp.ncbi.nih.gov/pub/pmc/" +
            " %s" % os.path.join(settings["DATADIR"], 'pmc/'),
            timeout=24*60*60
        )

class FetchPrintsJob(Job):
    def __init__(self):
        Job.__init__(self, "fetch_prints")

    def run(self):
        log_command(_log, 'prints',
            "/usr/bin/rsync -rtv --delete" +
            " --include=\'*.dat.gz\' --exclude=\'*\'" +
            " rsync://ftp.ebi.ac.uk/pub/databases/prints/" +
            " %s" % os.path.join(settings["DATADIR"], 'prints/'),
            timeout=24*60*60
        )

class FetchPrositeJob(Job):
    def __init__(self):
        Job.__init__(self, "fetch_prosite")

    def run(self):
        log_command(_log, 'prosite',
            "/usr/bin/rsync -rtv --delete --include=\'prosite*.dat\'" +
            " --include=\'prosite*.doc\' --exclude=\'*\'" +
            " rsync://ftp.ebi.ac.uk/pub/databases/prosite/" +
            " %s" % os.path.join(settings["DATADIR"], 'prosite/'),
            timeout=24*60*60
        )

class FetchRebaseJob(Job):
    def __init__(self):
        Job.__init__(self, "fetch_rebase")

    def run(self):
        with FTP('ftp.neb.com') as ftp:
            ftp.login()
            ftp.cwd('pub/rebase/')
            destdir = os.path.join(settings["DATADIR"], 'rebase')
            if not os.path.isdir(destdir):
                os.mkdir(destdir)
            with open(os.path.join(destdir, 'bairoch.txt'), 'wb') as f:
                _log.info("[rebase] retrieve bairoch.txt")
                ftp.retrbinary('RETR bairoch.txt', f.write)

class FetchRefseqJob(Job):
    def __init__(self):
        Job.__init__(self, "fetch_refseq")

    def run(self):
        log_command(_log, 'refseq',
            "/usr/bin/rsync -rtv --delete" +
            " --include=\'*g{p,b}ff.gz\' --exclude=\'*\'" +
            " rsync://ftp.ncbi.nih.gov/refseq/release/complete/" +
            " %s" % os.path.join(settings["DATADIR"], 'refseq/'),
            timeout=24*60*60
        )

class FetchTaxonomyJob(Job):
    def __init__(self):
        Job.__init__(self, "fetch_taxonomy")

    def run(self):
        with FTP('ftp.ebi.ac.uk') as ftp:
            ftp.login()
            ftp.cwd('pub/databases/taxonomy/')
            destdir = os.path.join(settings["DATADIR"], 'taxonomy')
            if not os.path.isdir(destdir):
                os.mkdir(destdir)
            with open(os.path.join(destdir,'taxonomy.dat'), 'wb') as f:
                _log.info("[taxonomy] retrieve taxonomy.dat")
                ftp.retrbinary('RETR taxonomy.dat', f.write)

class FetchUnigeneJob(Job):
    def __init__(self):
        Job.__init__(self, "fetch_unigene")

    def run(self):
        log_command(_log, 'unigene',
            "/usr/bin/rsync -rtv --delete" +
            " --include=\'*/\' --include=\'*.data.gz\' --exclude=\'*\'" +
            " rsync://ftp.ebi.ac.uk/pub/databases/Unigene/"
            " %s" % os.path.join(settings["DATADIR"], 'unigene/'),
            timeout=24*60*60
        )

class FetchEnzymeJob(Job):
    def __init__(self):
        Job.__init__(self, "fetch_enzyme")

    def run(self):
        log_command(_log, 'enzyme',
            "/usr/bin/rsync" +
            " rsync://ftp.ebi.ac.uk/pub/databases/enzyme/release_with_updates/"
            +
            " %s" % os.path.join(settings["DATADIR"], 'enzyme/'),
            timeout=24*60*60
        )
