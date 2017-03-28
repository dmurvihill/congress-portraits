# U.S. Congress portrait fetcher
This script crawls the Wikipedia API for portraits of every sitting
member of the United States Congress.

## Usage

The portrait fetcher is tested on Python 3.6. Python 2 is known
broken. With other Python versions, YMMV.

```bash
$ pip install -r requirements.txt
$ python get_portraits.py
```

The files will be downloaded into the working directory.

Unfortunately, the download fails for an appreciable fraction of the
politicians. Contributions gladly accepted.

## License

The portrait fetcher and documentation is in the public domain
(Unlicense). For the full public domain dedication, see the source
file itself.
