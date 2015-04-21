# photosort
Convert a directory tree of random images and sort by date and/or exif information.


## Motivation

The purpose of this tool is to take directories of badly organized photos (think iPhoto masters directory) and sort all photos based on the actual creation datestamp in the EXIF metadata.  Duplicates (based on the file's checksum) are ignored.  The resulting output is a directory tree of photos sorted by year / month / day.


## Details

When parsing the creation date, EXIF information is checked.  If the image is a RAW format, dcraw is used to extract the embedded jpeg and extract the EXIF tags from that.  The image file name is kept, and the image is copied to a new directory tree based on the creation date.


## Metadata

During execution, a small sqlite DB is created to store file checksums, etc.  This speeds up re-scanning of directories when looking for new files to import.  NO OTHER METADATA is kept.  For example, iPhoto event names, albums, original directory names, etc are not copied to the output directory.  If you want to tag these new pristine images, I recommend using the tagging feature of [Darktable](http://www.darktable.org/).


## Dependencies and Installation

You will first need to have:

* Python 3.x
* [exifread](https://pypi.python.org/pypi/ExifRead) module (pip3 install exifread)

And then you can install the package with:

```
$> python3 setup.py install --prefix=/path/to/somewhere
```

where the prefix should be in your PYTHONPATH.


## Usage

First make a directory for your output, sorted photos.  Then run the top-level photosync.py script:

```
$> python3 photosync --indir /path/to/crazy/photos --outdir ~/happy/sorted/photos
```

And then wait for a while.  If the photosync.db file in the output directory ever gets corrupted, just use the `--reindex` option to regenerate it.  You can run the command above whenever there are new photos added to the input directory, or run it multiple times on different input directories and the same output directory.  Only non-duplicates will be copied to the output directory.


## FAQ

1.  *But I want to save my hard work invested in tagging my photos using a proprietary software package.  Can't you do something?*

>  Sadly, no.  This is the eternal false promise of fancy closed-source applications.  They make some operations easier, but you lose control over your own data.

2.  

