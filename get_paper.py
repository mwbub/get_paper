#!/usr/bin/env python3

import sys
import os
import re
import requests

from textwrap import dedent
from argparse import ArgumentParser, RawDescriptionHelpFormatter


###################
# Functions
###################

def read_file(path):
    """
    Read a file's contents, and return an empty string if it does not exist.
    """
    if os.path.exists(path):
        with open(path, 'r') as file:
            text = file.read()
    else:
        text = ''
    
    return text


def make_dir(path):
    """
    Create a new directory at path. If the directory already exists, ignore it.
    """
    if not os.path.exists(path):
        os.mkdir(path)
    if not os.path.isdir(path):
        raise NotADirectoryError("{} is not a directory".format(path))


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
    
    
def to_snake(string):
    """
    Convert a string to snake_case.
    """
    return '_'.join(
        re.sub('([A-Z][a-z]+)', 
        r' \1', re.sub('([A-Z]+)', r' \1', 
        string.replace('-', ' '))).split()).lower()


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
        if bib[i] == '"' and bib[i-1] != '\\':
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
    bib = read_file(path)
    
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


def get_eprints(path):
    """
    Retrieve the eprint IDs from a .bib file.
    """
    bib = read_file(path)
    pattern = 'eprint\s*=[\s"{]*(\d+\.\d+|[a-zA-Z]+(-[a-zA-Z]+)?(\.[A-Z]{2})?\/\d+)(v\d+)?[\s"}]*'
    return [match[0] for match in re.findall(pattern, bib)]


###################
# Main
###################

def main(args, silent=False):
    
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
            
            The PDF will be saved to DIRECTORY/<Author><Year>_<Title>.pdf,
            where <Author> is the first-listed author's last name, <Year> is
            the year that the first version of the paper was released (not
            necessarily the publication year), and <Title> is the title of the
            the paper in PascalCase. If DIRECTORY does not exist, it will be
            created.
            
            If the option -b is provided, the BibTeX entry will be saved to
            DEST, which can either be a directory or a .bib file. Otherwise,
            the BibTeX entry will be saved to DIRECTORY. If DEST points to
            a directory which does not exist, it will be created. If -b is
            not provided or DEST does not point to a .bib file, a default
            filename will be generated.
            
            If the flag -u is set, any existing papers present in the BibTeX
            file with a valid arXiv identifier will be re-downloaded, and their
            corresponding BibTeX entries will be updated. An identifier option
            is not required in this case.
            """),
        formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('directory', help='destination directory', metavar='DIRECTORY')
    parser.add_argument('-a', '--arxiv', help='arXiv identifier')
    parser.add_argument('-d', '--doi', help='DOI')
    parser.add_argument('-i', '--inspire', help='INSPIRE literature identifier')
    parser.add_argument('-b', '--bib', dest='bib_dest', metavar='DEST',
                        help='bibliography destination or directory')
    parser.add_argument('-u', '--update', action='store_true', 
                        help='update existing papers')
    parser.add_argument('-n', '--nobib', action='store_true',
                        help="do not create or update a bibliography entry")
    args = parser.parse_args(args)
    
    # Determine the INSPIRE url given the provided options 
    id_provided = True
    if args.arxiv is not None:
        inspire_url = 'https://inspirehep.net/api/arxiv/{}'.format(args.arxiv)
    elif args.doi is not None:
        inspire_url = 'https://inspirehep.net/api/doi/{}'.format(args.doi)
    elif args.inspire is not None:
        inspire_url = 'https://inspirehep.net/api/literature/{}'.format(args.inspire)
    else:
        id_provided = False
    
    # Check that at least one identifier was provided
    if not id_provided and not args.update:
        parser.error('no identifier option provided')
    
    # Create the .bib filename from the provided options
    pdf_dir = os.path.abspath(args.directory)
    if args.bib_dest is None:
        bib_dir = pdf_dir
        bib_filename = to_snake(os.path.basename(pdf_dir)) + '.bib'
    else:
        bib_dest = os.path.abspath(args.bib_dest)
        if os.path.splitext(bib_dest)[1] == '.bib':
            bib_dir = os.path.dirname(bib_dest)
            bib_filename = os.path.basename(bib_dest)
        else:
            bib_dir = bib_dest
            bib_filename = to_snake(os.path.basename(pdf_dir)) + '.bib'
    bib_path = os.path.join(bib_dir, bib_filename)
    
    # Update existing pdfs and bib entries
    if args.update:
        update_eprints = get_eprints(bib_path)
        for count, update_eprint in enumerate(update_eprints):
            try:
                update_title = main(['-a', update_eprint, '-b', bib_path, pdf_dir], silent=True)
                print('Updated "{}" [arXiv:{}] [{}/{}]'.format(update_title, update_eprint, count+1, len(update_eprints)))
            except Exception as e:
                print('Could not update arXiv:{} because ' 
                      'of the following error: {} [{}/{}]'.format(update_eprint, e, count+1, len(update_eprints)))
        if not id_provided:
            quit()
    
    # Get the INSPIRE json for the paper
    r_inspire = requests.get(inspire_url)
    r_inspire.raise_for_status()
    
    # Get metadata and links from the json
    metadata = r_inspire.json()['metadata']
    links = r_inspire.json()['links']
    
    # Get the title and texkey
    title = metadata['titles'][0]['title']
    texkey = metadata['texkeys'][0]
    
    # Create the pdf filename
    pdf_filename = '{}_{}.pdf'.format(parse_texkey(texkey), to_pascal(title))
    pdf_path = os.path.join(pdf_dir, pdf_filename)
    
    # Get the pdf url, either from arxiv or directly from INSPIRE 
    if 'documents' in metadata:
        pdf_url = metadata['documents'][0]['url']
    else:
        eprint = metadata['arxiv_eprints'][0]['value']
        pdf_url = 'https://arxiv.org/pdf/{}.pdf'.format(eprint)
    
    # Get the pdf
    r_pdf = requests.get(pdf_url)
    r_pdf.raise_for_status()
        
    # Write the pdf to the appropriate file
    make_dir(pdf_dir) 
    with open(pdf_path, 'wb') as file:
        file.write(r_pdf.content)
        
    # Print a confirmation message
    if not silent:
        print('Saved paper to {}'.format(pdf_path))
        
    if not args.nobib:
        # Get the bibtex citation
        r_bibtex = requests.get(links['bibtex'])
        r_bibtex.raise_for_status()
        
        # Write the bibtex citation to the references file
        make_dir(bib_dir)
        bib = clean_bib(bib_path, delete_key=texkey) + r_bibtex.text
        with open(bib_path, 'w') as file:
            file.write(bib)
            
        # Print a confirmation message
        if not silent:
            print('Saved BibTeX citation to {}'.format(bib_path))
            
    return title


if __name__ == '__main__':
    main(sys.argv[1:])
