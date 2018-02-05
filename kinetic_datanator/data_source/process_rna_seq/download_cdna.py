from six.moves.urllib.request import urlretrieve
import os
import shutil


def run(sample, top_dir):
    """Downloads the CDNA for a given sample, and creates a kallisto index file. 
            The CDNA file is stored in a "CDNA" subdirectory within the top directory. 
            The kalliso index files are stored within "kallisto_index_files" subdirectory within the top directory

        Args:
            experiment(:obj:`array_express.Experiment`): the array express experiment
            top_dirname(:obj:`str`): the name of the directory where the overall data is being stored

        """
    DIRNAME = "{}/CDNA_FILES".format(top_dir)
    if not os.path.isdir(DIRNAME):
        os.makedirs(DIRNAME)
    spec_name = sample.ensembl_info[0].organism_strain
    file_name = "{}/{}.cdna.all.fa.gz".format(DIRNAME, spec_name)
    url = sample.ensembl_info[0].url
    if not os.path.isfile(file_name):
        file = urlretrieve(url, '{}/{}.cdna.all.fa.gz'.format(top_dir, spec_name))
        shutil.move('{}/{}.cdna.all.fa.gz'.format(top_dir, spec_name), DIRNAME)
    os.chdir(top_dir)
    KALLISTO_DIR = "{}/kallisto_index_files".format(top_dir)
    if not os.path.isdir(KALLISTO_DIR):
        os.makedirs(KALLISTO_DIR)
    if not os.path.isfile("{}/{}.idx".format(KALLISTO_DIR, spec_name)):
        os.system("kallisto index -i {}.idx {}".format(spec_name, file_name))
        shutil.move("{}/{}.idx".format(top_dir, spec_name), KALLISTO_DIR)
        