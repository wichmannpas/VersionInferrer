# VersionInferrer

## Requirements

- Python 3
- pip
- SQLite or PostgreSQL or both (for easier distribution of the index)


## Installation

Download VersionInferrer by cloning this repository, e.g. via

    git clone https://github.com/wichmannpas/VersionInferrer.git

Install the required Python packages via:

    pip install -r requirements.txt

Optional: If you want to use PostgreSQL, you need to install `psycopg2`:

    pip install psycopg2-binary

or `pip install --no-binary :all: psycopg2` (see [official documentation](http://initd.org/psycopg/docs/install.html#disabling-wheel-packages-for-psycopg-2-7)) if you want to build the binary yourself (requires a C toolchain).


## Configuration

Copy `settings_local.py.example` to `settings_local.py`.

Edit `settings_local.py` to override the default settings in `settings.py`, e.g. the configuration for PostgreSQL database name, user and password.


## Using a prepared Index

Under `Releases` of VersionInferrer's GitHub repository, there are ready to use indexes which are updated irregularily. By using these precomputed indexes, a lot of computing time is saved which is needed to create the index and this also saves a significant amount of disk space (~30 MB vs. ~5 GB).


## Creating the Index

Note: This step is **not** necessary if a prepared index is used!

Note: Initially, this takes quite a while! On a fairly modern computer (Intel Core i7 2.6 GHz, 16 GB RAM, NVMe SSD) it took about 4,5 hours! After that, subsequent runs of `./update_index.py` will only add versions that are not indexed, yet. This will result in much faster, incremental updates of the index.

Note: The index will take some disk space (~800 MB for the database and ~4 GB for the cache with different software versions). Therefore make sure to have enough disk space!

Simply run:

    ./update_index.py


### Distributing the Index

To distribute the index, the larger PostgreSQL database base can be squeezed into a much smaller SQLite database which is even smaller when compressed.

For converting the PostgreSQL database to SQLite, the `postgres_to_sqlite` in the project root can be used: `./postgres_to_sqlite POSTGRES_DB SQLITE_DB`


## Usage

Note: On first usage, VersionInferrer will download CVE statistics since 2002 up to now. Depending on your computer and network connection, this will take while (a few minutes).


### Single site

Run `./analyze_site.py` and pass a URL with the website to analyze, e.g.:

    ./analyze_site.py https://example.com

For more options see `./analyze_site.py --help`.


### Multiple sites

VersionInferrer includes a tool for scanning a large list of websites: `./scan_sites.py`.

This tool can either scan a manually submitted list in form of a text file with multiple URLs, each on a separate line, by specifiying the name of this file with the `--urls-from-file` option.

Alternatively, if no list is given, the Majestic Million list is taken automatically.

For further help and more options see `./scan_sites.py --help`.
