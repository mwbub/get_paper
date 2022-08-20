"""
Retrieve PDFs and BibTeX entries for papers from INSPIRE
"""
import os
import json
import requests

from argparse import ArgumentParser


###################
# Functions
###################

def parse_texkey(texkey):
    """Parse an INSPIRE texkey to remove the colon and the random letters at the end"""
    i = texkey.find(':')
    return texkey[:i] + texkey[i+1:i+5]


def to_pascal(string):
    """Convert a string to PascalCase, ignoring non-alphanumeric characters"""
    alphanumeric = ''.join([char if char.isalnum() else ' ' for char in string])
    return ''.join([word.title() if word.islower() else word for word in alphanumeric.split()])


def clean_bib(path, texkey):
    """Delete all entries from a .bib file with a given texkey"""
    if os.path.exists(path):

        # Read the lines of the file
        with open(path, 'r') as file:
            lines = file.readlines()

        # Rewrite lines to the file, but omit the given texkey
        with open(path, 'w') as file:
            
            delete = False
            for line in lines:

                # Begin deleting if the texkey is found
                if texkey in line:
                    delete = True

                if not delete:
                    file.write(line)

                # Stop deleting at the end of the entry
                if line == '\n':
                    delete = False


###################
# Main
###################

def main():

    # Parse the program options and arguments
    parser = ArgumentParser(
        description="""
            Download the PDF of a paper and add the BibTeX citation
            to a .bib file, using the INSPIRE database.
            """,
        epilog="""
            At least one identifier option is required to specify the 
            desired paper. If more than one option is provided, only 
            one will be used, and the rest will be ignored.
            """)
    parser.add_argument('directory', help='destination directory')
    parser.add_argument('-a', '--arxiv', help='arXiv identifier')
    parser.add_argument('-d', '--doi', help='DOI')
    parser.add_argument('-i', '--inspire', help='INSPIRE literature identifier')
    args = parser.parse_args()

    # Determine the INSPIRE url given the provided options 
    if args.arxiv is not None:
        inspire_url = 'https://inspirehep.net/api/arxiv/{}'.format(args.arxiv)
    elif args.doi is not None:
        inspire_url = 'https://inspirehep.net/api/doi/{}'.format(args.doi)
    elif args.inspire is not None:
        inspire_url = 'https://inspirehep.net/api/literature/{}'.format(args.inspire)
    else:
        raise parser.error('no options provided')

    # Get the INSPIRE json for the paper
    r_inspire = requests.get(inspire_url)
    r_inspire.raise_for_status()

    # Get metadata and links from the json
    metadata = r_inspire.json()['metadata']
    links = r_inspire.json()['links']

    # Get the title, texkey, and eprint id
    title = metadata['titles'][0]['title']
    texkey = metadata['texkeys'][0]
    eprint = metadata['arxiv_eprints'][0]['value']

    # Get the pdf url, either from arxiv or directly from INSPIRE 
    if 'documents' in metadata:
        pdf_url = metadata['documents'][0]['url']
    else:
        pdf_url = 'https://arxiv.org/pdf/{}.pdf'.format(eprint)

    # Get the pdf
    r_pdf = requests.get(pdf_url)
    r_pdf.raise_for_status()

    # Get the bibtex citation
    r_bibtex = requests.get(links['bibtex'])
    r_bibtex.raise_for_status()

    # Create a pdf filename from the title and texkey
    pdf_filename = '{}_{}.pdf'.format(parse_texkey(texkey), to_pascal(title))

    # Create the directory and ensure that it is valid
    pdf_dir = os.path.abspath(args.directory)
    if not os.path.exists(pdf_dir):
        os.mkdir(pdf_dir)
    if not os.path.isdir(pdf_dir):
        raise NotADirectoryError("{} is not a directory".format(pdf_dir))

    # Write the pdf to the appropriate file
    pdf_path = os.path.join(pdf_dir, pdf_filename)
    with open(pdf_path, 'wb') as file:
        file.write(r_pdf.content)
    print('Saved paper to {}'.format(pdf_path))

    # Write the bibtex citation to the references file
    bib_path = os.path.join(pdf_dir, 'references.bib')
    clean_bib(bib_path, texkey)
    with open(bib_path, 'a') as file:
        file.write(r_bibtex.text)
        file.write('\n')
    print('Saved BibTeX citation to {}'.format(bib_path))
    

if __name__ == '__main__':
    main()
