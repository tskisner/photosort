# photosort
Convert a directory tree of random images and sort by date and/or exif
information.


## Motivation

The purpose of this tool is to take directories of badly organized photos
(think iPhoto masters directory) and sort all photos based on the actual
creation datestamp in the EXIF metadata.  Duplicates (based on the file's
checksum) are ignored.  The resulting output is a directory tree of photos
sorted by year / month / day.


## Details

When parsing the creation date, EXIF information is checked.  If the image is
a RAW format, dcraw is used to extract the embedded jpeg and extract the EXIF
tags from that.  The image file name is kept, and the image is copied to a new
directory tree based on the creation date.


## Metadata

During execution, a small sqlite DB is created to store file checksums, etc.  
This speeds up re-scanning of directories when looking for new files to import.  
NO OTHER METADATA is kept.  For example, iPhoto event names, albums, original
directory names, etc are not copied to the output directory.  If you want to
tag these new pristine images, I recommend using the tagging feature
of [Darktable](http://www.darktable.org/).


## Dependencies and Installation

You should have a fairly recent version of python3 installed.  Additionally,
you will need some external command-line tools:

1.  exiftool (REQUIRED)
2.  dcraw (if using RAW images)
3.  ffmpeg (if converting old videos)
4.  ImageMagick (if exporting images to reduced resolutions)


## Usage

There are several small commandline scripts provided.

### Sorting

Decide where you would like to output the sorted files, then run (for example):

```
$> phts_sync --indir /path/to/crazy/photos --outdir ~/happy/sorted/photos
```

And then wait for a while.  If the photosync.db file in the output directory
ever gets corrupted, just use the `--reindex` option to phts_sync to regenerate
it.  You can run the command above whenever there are new photos added to the
input directory, or run it multiple times on different input directories and
the same output directory.  Only non-duplicates will be copied to the output
directory.

### Verify

When indexing, files are checksummed and a short version of that hash is put
into the filename and the database.  This makes it possible to verify that the
*contents* of the image files have not changed.  This should detect some kinds
of disk corruption where the file size and access times are correct, but some
bytes of the file have been changed:

```
$> phts_verify --outdir ~/happy/sorted/photos
```

### Albums

Albums are handy.  I typically use symbolic links for these, and there is a
useful script included here for this purpose (phts_album).  Usually I specify
the album directory options and then for the file names I select the files I
want using a file browser and drag them to my terminal window.  For many Linux
desktop environments this copies the paths to the files into the terminal, and
then simply press enter.


## FAQ

-  *But I want to save my hard work invested in tagging my photos using a
    proprietary software package.  Can't you do something?*

>  Sadly, no.  This is the eternal false promise of fancy closed-source
    applications.  They make some operations easier, but you lose control over
    your own data.

-  *Can't you add feature XXXX?*

>  Why don't you implement it and send me a pull request?  
