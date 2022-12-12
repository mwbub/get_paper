# get_paper

`get_paper.py` is a Python script which retrieves physics papers and BibTeX entries from the INSPIRE database. It can automatically download and save PDFs of papers and update a .bib file with the corresponding entry. PDFs are saved with a descriptive title, and BibTeX entries use the INSPIRE format.

The script currently only works with papers that are available on arXiv. If the INSPIRE entry contains the full text of the published version of a paper, the script will attempt to download that. Otherwise, it will download the arXiv version.

## Installation
Simply clone the repository or directly download `get_paper.py` anywhere you'd like. If desired, you can add the script location to your `PATH` environment variable, or download to `/usr/local/bin`, for access anywhere on the command line.

## Usage
```
usage: get_paper.py [-h] [-a ARXIV] [-d DOI] [-i INSPIRE] [-b DEST] [-u] [-n] DIRECTORY

positional arguments:
  DIRECTORY                         destination directory

optional arguments:
  -h, --help                        show this help message and exit
  -a ARXIV, --arxiv ARXIV           arXiv identifier
  -d DOI, --doi DOI                 DOI
  -i INSPIRE, --inspire INSPIRE     INSPIRE literature identifier
  -b DEST, --bib DEST               bibliography destination or directory
  -u, --update                      update existing papers
  -n, --nobib                       do not create or update a bibliography entry
```
At least one identifier option `-a`, `-d`, or `-i` is required to specify
the desired paper. If more than one of `-a`, `-d`, or `-i` is provided,
only the first in the order listed above will be used.

The PDF will be saved to `DIRECTORY/<Author><Year>_<Title>.pdf`,
where `<Author>` is the first-listed author's last name, `<Year>` is
the year that the first version of the paper was released (not
necessarily the publication year), and `<Title>` is the title of the
the paper in PascalCase. If `DIRECTORY` does not exist, it will be
created.

If the option `-b` is provided, the BibTeX entry will be saved to
`DEST`, which can either be a directory or a .bib file. Otherwise,
the BibTeX entry will be saved to `DIRECTORY`. If `DEST` points to
a directory which does not exist, it will be created. If `-b` is
not provided or `DEST` does not point to a .bib file, a default
filename will be generated.

If the flag `-u` is set, any existing papers present in the BibTeX
file with a valid arXiv identifier will be re-downloaded, and their
corresponding BibTeX entries will be updated. An identifier option
is not required in this case.

## Examples
### Using an arXiv identifier: 

`get_paper.py -a hep-th/9711200 paper_dir`

This will download the paper to `./paper_dir/Maldacena1997_TheLargeNLimitOfSuperconformalFieldTheoriesAndSupergravity.pdf`, and the BibTeX entry to `./paper_dir/paper_dir.bib`. If `paper_dir.bib` already exists, it will be updated with the new entry, and repeated entries will be deleted. The .bib file will also be reformatted with consistent whitespace.

### Using a DOI:

`get_paper.py -d 10.1023/A:1026654312961 paper_dir`

This will have the same effect as above.

### Using an INSPIRE literature identifier:

`get_paper.py -i 451647 paper_dir`

This will also have the same effect as above.

### Specifying a .bib file:

`get_paper.py -a 1207.7214 -b bib_dir paper_dir`

This will save the BibTeX entry to `./bib_dir/paper_dir.bib`, and `bib_dir` will be created if it does not exist.

`get_paper.py -a 1207.7214 -b bib_dir/references.bib paper_dir`

Similarly, this will save the BibTeX entry to `./bib_dir/references.bib`, and `bib_dir` will be created if it does not exist.

### Updating existing papers:

`get_paper.py -u -b bib_dir/references.bib paper_dir`

This will find all arXiv identifiers in `./bib_dir/references.bib`, re-download the latest versions of the corresponding papers to `./paper_dir/`, and update the BibTeX entries. This can be used to update papers and BibTeX entries in case a new version of a paper is released, or if a preprint is published in a journal. It can also be used to download papers en masse from a BibTeX file.

`get_paper.py -u -a 1207.7214 paper_dir`

This will update the papers found in `./paper_dir/paper_dir.bib`, and also download the paper with arXiv identifier 1207.7214.

## Bugs and Feature Requests
Please submit an [issue](https://github.com/mwbub/get_paper/issues) if you encounter any bugs or have a suggestion.
