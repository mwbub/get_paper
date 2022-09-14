# get_paper

`get_paper.py` is a Python script which retrieves physics papers and BibTeX entries from the INSPIRE database. It can automatically download and save PDFs of papers and update a .bib file with the corresponding entry. PDFs are saved with a descriptive title, and BibTeX entries use the INSPIRE format.

The script currently only works with papers that are available on arXiv. If the INSPIRE entry contains the full text of the published version of a paper, the script will attempt to download that. Otherwise, it will download the arXiv version.

## Installation
Simply clone the repository or directly download `get_paper.py` anywhere you'd like. If desired, you can add the script location to your `PATH` environment variable, or download to `/usr/local/bin`, for access anywhere on the command line.

## Usage
```
usage: get_paper.py [-h] [-a ARXIV] [-d DOI] [-i INSPIRE] [-b DEST] directory

positional arguments:
  directory                         destination directory

optional arguments:
  -h, --help                        show this help message and exit
  -a ARXIV, --arxiv ARXIV           arXiv identifier
  -d DOI, --doi DOI                 DOI
  -i INSPIRE, --inspire INSPIRE     INSPIRE literature identifier
  -b DEST, --bib DEST               bibliography destination or directory
```
At least one identifier option `-a`, `-d`, or `-i` is required to specify
the desired paper. If more than one of `-a`, `-d`, or `-i` is provided,
only the first in the order listed above will be used.

The PDF will be saved to `directory/<Author><Year>_<Title>.pdf`,
where `<Author>` is the first-listed author's last name, `<Year>` is
the year that the first version of the paper was released (not
necessarily the publication year), and `<Title>` is the title of the
the paper in PascalCase. If `directory` does not exist, it will be
created.

If the option `-b` is not provided, the BibTeX entry will be saved to
`directory/references.bib`. Otherwise, the BibTeX entry will be
saved to `DEST` or `DEST/references.bib`, depending on whether `DEST`
is a path to a .bib file or to a directory. If `DEST` points to a
directory which does not exist, it will be created.

## Examples
### Using an arXiv identifier: 

`get_paper.py -a hep-th/9711200 paper_dir`

This will download the paper to `./paper_dir/Maldacena1997_TheLargeNLimitOfSuperconformalFieldTheoriesAndSupergravity.pdf`, and the BibTeX entry to `./paper_dir/references.bib`. If `references.bib` already exists, it will be updated with the new entry, and repeated entries will be deleted. The .bib file will also be reformatted with consistent whitespace.

### Using a DOI:

`get_paper.py -d 10.1023/A:1026654312961 paper_dir`

This will have the same effect as above.

### Using an INSPIRE literature identifier:

`get_paper.py -i 451647 paper_dir`

This will also have the same effect as above.

### Specifying a .bib file:

`get_paper.py -a 1207.7214 -b bib_dir paper_dir`

This will save the BibTeX entry to `./bib_dir/references.bib`, and `bib_dir` will be created if it does not exist.

`get_paper.py -a 1207.7214 -b bib_dir/bibliography.bib paper_dir`

Similarly, this will save the BibTeX entry to `./bib_dir/bibliography.bib`, and `bib_dir` will be created if it does not exist.

## Bugs and Feature Requests
Please submit an [issue](https://github.com/mwbub/get_paper/issues) if you encounter any bugs or have a suggestion.
