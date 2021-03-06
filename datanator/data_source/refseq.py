"""
import pprint
from Bio import SeqIO
import datetime
import dateutil.parser
import pkg_resources
import sqlalchemy
import sqlalchemy.ext.declarative
import sqlalchemy.orm
from datanator.core import data_source
"""
import sqlalchemy
import sqlalchemy.ext.declarative
import sqlalchemy.orm
from datanator.core import data_source
from Bio import SeqIO
import Bio
import json
import math
import tempfile
import os
import gzip
import shutil
from six.moves.urllib.request import urlretrieve
import json
Base = sqlalchemy.ext.declarative.declarative_base()

def create_orm(class_1, class_2):
    
    new_table = sqlalchemy.Table(
    "{}_{}".format(class_1,class_2), Base.metadata,
    sqlalchemy.Column('{}{}_id'.format(class_1[0].lower(), class_1[1:]), sqlalchemy.Integer, sqlalchemy.ForeignKey('{}{}._id'.format(class_1[0].lower(), class_1[1:])), index=True),
    sqlalchemy.Column('{}{}_id'.format(class_2[0].lower(), class_2[1:]), sqlalchemy.Integer, sqlalchemy.ForeignKey('{}{}._id'.format(class_2[0].lower(), class_2[1:])), index=True),
    )
    
    return sqlalchemy.orm.relationship(class_2, secondary=new_table, backref=sqlalchemy.orm.backref('{}{}'.format(class_1[0].lower(), class_1[1:])))


class Location(Base):
    _id = sqlalchemy.Column(sqlalchemy.Integer(), primary_key=True)
    _end = sqlalchemy.Column(sqlalchemy.Integer())
    _start = sqlalchemy.Column(sqlalchemy.Integer())
    end = sqlalchemy.Column(sqlalchemy.Integer())
    nofuzzy_end = sqlalchemy.Column(sqlalchemy.Integer())
    nofuzzy_start = sqlalchemy.Column(sqlalchemy.Integer())
    ref = sqlalchemy.Column(sqlalchemy.String())
    ref_db = sqlalchemy.Column(sqlalchemy.String())
    start = sqlalchemy.Column(sqlalchemy.Integer())
    strand = sqlalchemy.Column(sqlalchemy.Integer())

    __tablename__ = 'location'

class Qualifier(Base):
    _id = sqlalchemy.Column(sqlalchemy.Integer(), primary_key=True)
    key = sqlalchemy.Column(sqlalchemy.String())
    value = sqlalchemy.Column(sqlalchemy.String())

    __tablename__ = 'qualifier'

class GeneSynonym(Base):
    _id = sqlalchemy.Column(sqlalchemy.Integer(), primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String())
    __tablename__ = 'geneSynonym'

class EcNumber(Base):
    _id = sqlalchemy.Column(sqlalchemy.Integer(), primary_key=True)
    ec_number = sqlalchemy.Column(sqlalchemy.String())
    __tablename__ = 'ecNumber'

class Identifier(Base):
    _id = sqlalchemy.Column(sqlalchemy.Integer(), primary_key=True)
    namespace = sqlalchemy.Column(sqlalchemy.String())
    name = sqlalchemy.Column(sqlalchemy.String())
    __tablename__ = 'identifier'


class Gene(Base):
    _id = sqlalchemy.Column(sqlalchemy.Integer(), primary_key=True)
    id = sqlalchemy.Column(sqlalchemy.String())
    ref_genome_version = sqlalchemy.Column(sqlalchemy.String())
    name = sqlalchemy.Column(sqlalchemy.String())
    locus_tag = sqlalchemy.Column(sqlalchemy.String())
    gene_synonyms = create_orm("Gene", "GeneSynonym")
    location = create_orm("Gene", "Location")
    qualifiers = create_orm('Gene','Qualifier')
    ec_numbers = create_orm('Gene','EcNumber')
    identifiers = create_orm('Gene', 'Identifier')
    essentiality = sqlalchemy.Column(sqlalchemy.String())
    __tablename__ = 'gene'


class ReferenceGenome(Base):
    _id = sqlalchemy.Column(sqlalchemy.Integer(), primary_key=True)
    accessions = create_orm("ReferenceGenome", "ReferenceGenomeAccession")
    #accession = sqlalchemy.Column(sqlalchemy.String())
    version = sqlalchemy.Column(sqlalchemy.String())
    organism = sqlalchemy.Column(sqlalchemy.String())
    genes = create_orm("ReferenceGenome", "Gene")#sqlalchemy.orm.relationship('GeneSynonym', secondary=gene_gene_synonym, backref=sqlalchemy.orm.backref('genes'))


    __tablename__ = 'referenceGenome'


class ReferenceGenomeAccession(Base):
    _id = sqlalchemy.Column(sqlalchemy.Integer(), primary_key=True)
    id = sqlalchemy.Column(sqlalchemy.String())

    __tablename__ = 'referenceGenomeAccession'

class Refseq(data_source.HttpDataSource):
    base_model = Base


    def __init__(self, name=None, cache_dirname=None, clear_content=False, load_content=False, max_entries=float('inf'),
                 commit_intermediate_results=False, download_backups=False, verbose=False,
                 clear_requests_cache=False, download_request_backup=False,
                 quilt_owner=None, quilt_package=None):

        super(Refseq, self).__init__(name=name, cache_dirname=cache_dirname, clear_content=clear_content,
                                           load_content=load_content, max_entries=max_entries,
                                           commit_intermediate_results=commit_intermediate_results,
                                           download_backups=download_backups, verbose=verbose,
                                           clear_requests_cache=clear_requests_cache, download_request_backup=download_request_backup,
                                           quilt_owner=quilt_owner, quilt_package=quilt_package)

    def get_paths_to_backup(self, download=False):
        """ Get a list of the files to backup/unpack

        Args:
            download (:obj:`bool`, optional): if :obj:`True`, prepare the files for uploading

        Returns:
            :obj:`list` of :obj:`str`: list of paths to backup
        """
        paths = []
        paths.append('refseq/')
        return paths

    def load_content(self, list_bio_seqio_objects):
        session = self.session
        for bio_seqio_object in list_bio_seqio_objects:
            for seq_record in bio_seqio_object:
                ref_genome = self.get_or_create_object(ReferenceGenome,
                    version = seq_record.id
                    )
                if 'accessions' in seq_record.annotations:
                    for accession in seq_record.annotations['accessions']:
                        print(accession)
                        acc = self.get_or_create_object(ReferenceGenomeAccession,
                            id=accession)
                        ref_genome.accessions.append(acc)
                ref_genome.version = seq_record.id
                if 'organism' in seq_record.annotations:
                    ref_genome.organism = seq_record.annotations['organism']
                #session.add(ref_genome)
                i = 0
                for seq_feature in seq_record.features:
                    if seq_feature.type == 'CDS':
                        i = i +1
                        #print(i)


                        #gene = self.get_or_create_object(Gene,)
                        locus_tag = seq_feature.qualifiers['locus_tag'][0]
                        if len(seq_feature.qualifiers['locus_tag']) != 1:
                            raise ValueError("There must be one, and only one, locus tag")
                        gene = self.get_or_create_object(Gene,
                            ref_genome_version = ref_genome.version,
                            locus_tag = locus_tag)
                        #gene = Gene()
                        gene.id = seq_feature.id
                        
                        parts = []
                        if type(seq_feature.location)==Bio.SeqFeature.FeatureLocation:
                            parts.append(seq_feature.location)

                        elif type(seq_feature.location)==Bio.SeqFeature.CompoundLocation:
                            x = seq_feature
                            for part in seq_feature.location.parts:
                                parts.append(part)
                        for part in parts:
                            location = Location()
                            location._end = part._end
                            location._start = part._start
                            location.end = part.end
                            location.nofuzzy_end = part.nofuzzy_end
                            location.nofuzzy_start = part.nofuzzy_start
                            location.ref = part.ref
                            location.ref_db = part.ref_db
                            location.start = part.start
                            location.strand = part.strand
                            session.add(location)
                            gene.location.append(location)

                        qual = seq_feature.qualifiers
                        #print(seq_feature.qualifiers)
                        if 'gene' in qual:
                            gene.name = qual['gene'][0]
                            if len(qual['gene'])>1:
                                raise ValueError("More than one value")
                        if "gene_synonym" in qual:
                            for name in qual['gene_synonym']:
                                for embedded_name in name.split(";"):
                                    gene_synonym = self.get_or_create_object(GeneSynonym,
                                        name = embedded_name)
                                    gene.gene_synonyms.append(gene_synonym)
                        if 'EC_number' in qual:
                            for number in qual['EC_number']:
                                ec_number = self.get_or_create_object(EcNumber, 
                                    ec_number = number)
                                gene.ec_numbers.append(ec_number)
                        if 'db_xref' in qual:
                            for identifier in qual['db_xref']:
                                if len(identifier)>3: #make sure its not nan
                                    identifier = self.get_or_create_object(Identifier,
                                        namespace = identifier.split(":")[0],
                                        name = identifier.split(":")[1])
                                    gene.identifiers.append(identifier)

                        #if 'locus_tag' in qual:
                         #   gene.locus_tag = qual['locus_tag'][0]
                         #   if len(qual['locus_tag'])>1:
                         #       raise ValueError("More than one value")
                        if 'essentiality2016_assigned' in qual:
                            gene.essentiality = qual['essentiality2016_assigned'][0]

                            
                        session.add(gene)
                        ref_genome.genes.append(gene)
                    elif seq_feature.type == 'source':
                        pass
                    else: 
                        pass

                        #to do: finish this up. its metadata on the reference genome

        self.session.commit()

    def upload_data_from_kegg_org_symbol(self, kegg_org_symbol):
        # get FTP URL for sequence
        url = self.get_ref_seq_url(kegg_org_symbol)

        # create directory to store sequence files
        dirname = os.path.join(self.cache_dirname, 'refseq')
        if not os.path.isdir(dirname):
            os.mkdir(dirname)

        # download sequence
        filename = os.path.join(dirname, "{}.gbff.gz".format(kegg_org_symbol))
        attempts = 0
        while attempts < 10:
            try:
                urlretrieve(url, filename)
                break
            except Exception as err:
                attempts += 1
                if attempts == 10:
                    raise err
        
        # unzip sequence file
        with gzip.open('{}'.format(filename, 'rb')) as f_in:
            with open('{}'.format(filename[:-3]), 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        # parse sequence file
        bio_seqio_object = SeqIO.parse(filename[:-3], "genbank")
        list_of_bio_seqio_objects = [bio_seqio_object]
        self.load_content(list_of_bio_seqio_objects)

        # delete temporary unzipped file
        os.remove(filename[:-3])

    def upload_ref_seq_for_all_prokaryotic_kegg_org(self):
        with open(os.path.join(os.path.dirname(__file__), 'kegg_taxon_prokaryotes.txt')) as file:
            data = json.load(file)
        for thing in self.get_json_ends(data):
            kegg_org_symbol = thing.split('  ')[0]
            self.upload_data_from_kegg_org_symbol(kegg_org_symbol)

    def get_json_ends(self, tree):
        ends = []
        nodes = [tree]
        while nodes:
            new_nodes = []
            for node in nodes:
                if 'children' in node:
                    new_nodes = new_nodes + node['children']
                else:
                    ends.append(node['name'])
            nodes = new_nodes
        return(ends)

    def get_ref_seq_url(self, org_symbol):
        text = self.requests_session.get("http://www.kegg.jp/kegg-bin/show_organism?org={}".format(org_symbol)).text
        text = text[text.find("ftp://ftp.ncbi.nlm.nih.gov/genomes/all"):]
        text = text[:text.find("""">""")]
        end = text[self.find_nth(text, "/", 9)+1:]
        text = "{}/{}_genomic.gbff.gz".format(text, end)
        return text


    def get_or_create_object(self, cls, **kwargs):
        """ Get the first instance of :obj:`cls` that has the property-values pairs described by kwargs, or create an instance of :obj:`cls`
        if there is no instance with the property-values pairs described by kwargs
        Args:
            cls (:obj:`class`): type of object to find or create
            **kwargs: values of the properties of the object
        Returns:
            :obj:`Base`: instance of :obj:`cls` hat has the property-values pairs described by kwargs
        """
        q = self.session.query(cls).filter_by(**kwargs)
        if self.session.query(q.exists()).scalar():
            return q.first()

        obj = cls(**kwargs)
        self.session.add(obj)
        return obj


    def find_nth(self, haystack, needle, n):
        start = haystack.find(needle)
        while start >= 0 and n > 1:
            start = haystack.find(needle, start+len(needle))
            n -= 1
        return start

if __name__ == '__main__':

    filenames = [
            "/home/yosef/Desktop/Genome_Database/mpn_annotation.gbff",
            #"/home/yosef/Desktop/Genome_Database/sequence.gb",
            ]
    get_genes = Refseq(cache_dirname = '/home/yosef/Desktop/Genome_Database')
    get_genes.load_content(filenames)
