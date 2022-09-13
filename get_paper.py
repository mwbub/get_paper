#!/usr/bin/env python3

import os
import re
import json
import requests

from textwrap import dedent
from argparse import ArgumentParser, RawDescriptionHelpFormatter


###################
# Functions
###################

def parse_texkey(texkey):
    """
    Parse an INSPIRE texkey to remove the colon and the random letters at the end.
    """
    i = texkey.find(':')
    return texkey[:i] + texkey[i+1:i+5]


def to_pascal(string):
    """
    Convert a string to PascalCase, ignoring non-alphanumeric characters.
    """
    alphanumeric = ''.join([char if char.isalnum() else ' ' for char in string])
    return ''.join([word.title() if word.islower() else word for word in alphanumeric.split()])


def replace_interior(bib):
    """
    Replace commas, equals signs, and right curly braces which appear in quoted
    or curly-braced text in a .bib file's text with the placeholders '<COMMA>',
    '<EQUALS>', and '<RCURLY>', respectively.
    """
    # Start at 0 levels of quotes/braces
    level = 0
    start_quote = True
    
    # Iterate backwards through the string
    for i in range(len(bib)-1, -1, -1):
        
        # Replace commas 2 or more layers deep with the placeholder
        if bib[i] == ',' and level > 1:
            bib = bib[:i] + '<COMMA>' + bib[i+1:]
        
        # Replace equals signs 2 or more layers deep with the placeholder
        if bib[i] == '=' and level > 1:
            bib = bib[:i] + '<EQUALS>' + bib[i+1:]
        
        # Increase the level if a right curly brace is found
        if bib[i] == '}':
            # Replace interior right curly braces with the placeholder
            if level > 0:
                bib = bib[:i] + '<RCURLY>' + bib[i+1:]
            level += 1
        
        # Decrease the level if a left curly brace is found
        if bib[i] == '{':
            level -= 1
        
        # Increase the level if starting a quote, decrease if ending
        if bib[i] == '"':
            if start_quote:
                level += 1
                start_quote = False
            else:
                level -= 1
                start_quote = True
    
    # Ensure that all quotations and curly braces are closed
    if level != 0 or not start_quote:
        raise SyntaxError('unpaired quotation or curly brace in .bib file')
    
    return bib


def restore_interior(bib):
    """
    Restore the commas, equals signs, and right curly braces that were replaced
    with placeholder text by replace_interior().
    """
    bib = re.sub('<COMMA>', ',', bib)
    bib = re.sub('<EQUALS>', '=', bib)
    bib = re.sub('<RCURLY>', '}', bib)
    return bib


def clean_bib(path, delete_key=None):
    """
    Reformat a .bib file's text with the correct spacing, and optionally delete
    all entries with the key delete_key.
    """
    # Read the bib file if it exists
    if os.path.exists(path):
        with open(path, 'r') as file:
            bib = file.read()
    else:
        bib = ''
    
    # Reformat the bib text
    bib = bib.lstrip()                          # Remove leading whitespace
    bib = replace_interior(bib)                 # Replace interior quotes/braces
    bib = re.sub('(\s)*,(\s)*', ',\n    ', bib) # Fix spacing around commas
    bib = re.sub('(\s)*=(\s)*', ' = ', bib)     # Fix spacing around equals signs
    bib = re.sub('(\s)*}(\s)*', '\n}\n\n', bib) # Fix spacing around right curly braces
    
    # Delete all bib entries with key delete_key
    if delete_key is not None:
        bib = re.sub('@(\w)+\{{{}(.|\n)+?\}}\n\n'.format(delete_key), '', bib)
    
    bib = restore_interior(bib) # Restore interior quotes/braces
    
    return bib


def make_dir(path):
    """
    Create a new directory at path. If the directory already exists, ignore it.
    """
    if not os.path.exists(path):
        os.mkdir(path)
    if not os.path.isdir(path):
        raise NotADirectoryError("{} is not a directory".format(path))


###################
# Main
###################

def main():

    # Parse the program options and arguments
    parser = ArgumentParser(
        description=dedent("""
            Download the PDF of a paper and add the BibTeX citation to a .bib
            file, using the INSPIRE database.
            """),
        epilog=dedent("""
            At least one identifier option -a, -d, or -i is required to specify
            the desired paper. If more than one of -a, -d, or -i is provided,
            only the first in the order listed above will be used.
            
            The PDF will be saved to "directory/<Author><Year>_<Title>.pdf",
            where <Author> is the first-listed author's last name, <Year> is
            the year that the first version of the paper was released (not
            necessarily the publication year), and <Title> is the title of the
            the paper in PascalCase. If directory does not exist, it will be
            created.
            
            If the option -b is not provided, the BibTeX entry will be saved to
            "directory/references.bib". Otherwise, the BibTeX entry will be
            saved to "DEST" or "DEST/references.bib", depending on whether DEST
            is a path to a .bib file or to a directory. If DEST is a directory
            which does not exist, it will be created.
            """),
        formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('directory', help='destination directory')
    parser.add_argument('-a', '--arxiv', help='arXiv identifier')
    parser.add_argument('-d', '--doi', help='DOI')
    parser.add_argument('-i', '--inspire', help='INSPIRE literature identifier')
    parser.add_argument('-b', '--bib-destination', dest='bib_dest', metavar='DEST', 
                        help='bibliography destination or directory')
    args = parser.parse_args()
    
    # Determine the INSPIRE url given the provided options 
    if args.arxiv is not None:
        inspire_url = 'https://inspirehep.net/api/arxiv/{}'.format(args.arxiv)
    elif args.doi is not None:
        inspire_url = 'https://inspirehep.net/api/doi/{}'.format(args.doi)
    elif args.inspire is not None:
        inspire_url = 'https://inspirehep.net/api/literature/{}'.format(args.inspire)
    else:
        parser.error('no identifier option provided')
    
    # Get the INSPIRE json for the paper
    r_inspire = requests.get(inspire_url)
    r_inspire.raise_for_status()
    
    # Get metadata and links from the json
    metadata = r_inspire.json()['metadata']
    links = r_inspire.json()['links']
    
    # Get the title and texkey
    title = metadata['titles'][0]['title']
    texkey = metadata['texkeys'][0]
    
    # Get the pdf url, either from arxiv or directly from INSPIRE 
    if 'documents' in metadata:
        pdf_url = metadata['documents'][0]['url']
    else:
        eprint = metadata['arxiv_eprints'][0]['value']
        pdf_url = 'https://arxiv.org/pdf/{}.pdf'.format(eprint)
    
    # Get the pdf
    r_pdf = requests.get(pdf_url)
    r_pdf.raise_for_status()
    
    # Get the bibtex citation
    r_bibtex = requests.get(links['bibtex'])
    r_bibtex.raise_for_status()
    
    # Create the pdf filename and directory
    pdf_dir = os.path.abspath(args.directory)
    pdf_filename = '{}_{}.pdf'.format(parse_texkey(texkey), to_pascal(title))
    pdf_path = os.path.join(pdf_dir, pdf_filename)
    make_dir(pdf_dir)
    
    # Create the .bib filename and directory from the provided options
    if args.bib_dest is None:
        bib_dir = pdf_dir
        bib_filename = 'references.bib'
    else:
        bib_dest = os.path.abspath(args.bib_dest)
        if os.path.splitext(bib_dest)[1] == '.bib':
            bib_dir = os.path.dirname(bib_dest)
            bib_filename = os.path.basename(bib_dest)
        else:
            bib_dir = bib_dest
            bib_filename = 'references.bib'
    bib_path = os.path.join(bib_dir, bib_filename)    
    make_dir(bib_dir)
    
    # Write the pdf to the appropriate file
    with open(pdf_path, 'wb') as file:
        file.write(r_pdf.content)
    print('Saved paper to {}'.format(pdf_path))
    
    # Write the bibtex citation to the references file
    bib = clean_bib(bib_path, delete_key=texkey) + r_bibtex.text
    with open(bib_path, 'w') as file:
        file.write(bib)
    print('Saved BibTeX citation to {}'.format(bib_path))


if __name__ == '__main__':
    main()
