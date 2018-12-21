# VersionInferrer

## Requirements

- Python 3
- pip
- SQLite or PostgreSQL


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


## Creating the Index

Note: Initially, this takes quite a while! On a fairly modern computer (Intel Core i7 2.6 GHz, 16 GB RAM, NVMe SSD) it took about 4,5 hours! After that, subsequent runs of `./update_index.py` will only add versions that are not indexed, yet. This will result in much faster, incremental updates of the index.

Note: The index will take some disk space (about 780 MB). Make sure to have enough disk space.

Simply run:

    ./update_index.py


## Usage

Note: On first usage, VersionInferrer will download CVE statistics since 2002 up to now. Depending on your computer and network connection, this will take while (a few minutes).

Run `./analyze_site.py` and pass a URL with the website to analyze, e.g.:

    ./analyze_site.py https://example.com

For more options see `./analyze_site.py --help`.
