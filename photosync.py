
import os
import sys
import shutil
import re
import argparse

import photosort as ps


def index_images(db, dir, files):
    # If images are manually moved to new directories (for example,
    # due to bad EXIF data), then we want to preserve those changes
    # when re-indexing.
    (temp, day) = os.path.split(dir)
    (temp, month) = os.path.split(temp)
    (temp, year) = os.path.split(temp)
    infile = os.path.abspath( os.path.join(dir, f) )
    for f in files:
        img = ps.Image(infile, year=year, month=month, day=day)
        db.insert(img)


def import_images(db, indir, files, outroot):
    for f in files:
        mat = re.match('(.*)\.(.*)', f)
        if not mat:
            continue
        ext = mat.group(2)
        if ext.lower() not in ps.image_ext:
            continue
        infile = os.path.abspath( os.path.join(indir, f) )
        chk = ps.image_md5(infile)
        print('checking {}'.format(infile))
        if (not db.query_md5(chk)):
            img = ps.Image(infile)
            yeardir = os.path.join(outroot, img.year)
            monthdir = os.path.join(yeardir, img.month)
            daydir = os.path.join(monthdir, img.day)
            if not os.path.isdir(outroot):
                os.mkdir(outroot)
            if not os.path.isdir(yeardir):
                os.mkdir(yeardir)
            if not os.path.isdir(monthdir):
                os.mkdir(monthdir)
            if not os.path.isdir(daydir):
                os.mkdir(daydir)

            result = db.query(img.uid)
            if result is None:
                outfile = os.path.abspath( os.path.join(daydir, img.name) )
                if infile != outfile:
                    print('  copying to {}'.format(outfile))
                    shutil.copy2(infile, outfile)
                print('  adding to DB')
                db.insert(img)
            else:
                # Uh-oh.  We have a file with the same name
                # and date as an existing image, but with a
                # DIFFERENT checksum!  Print a warning and
                # copy it to a new name.
                print('  WARNING: file with same name and date but different checksum found')
                print('  WARNING: copying to file name based on checksum to avoid overwrite.')
                outfile = os.path.abspath( os.path.join(daydir, img.root) ) + '_DUP_' + chk + '.' + img.ext
                if infile != outfile:
                    print('  copying to {}'.format(outfile))
                    shutil.copy2(infile, outfile)
                # instantiate a new image on this, before adding to DB
                newimg = ps.Image(outfile)
                db.insert(newimg)
        else:
            print('  found in DB')


def main():
    parser = argparse.ArgumentParser( description='Organize photos by EXIF data.' )
    parser.add_argument( '--indir', required=False, default='', help='input directory' )
    parser.add_argument( '--outdir', required=True, default='', help='output directory' )
    parser.add_argument( '--reindex', required=False, default=False, action='store_true', help='force rebuild of index' )
    args = parser.parse_args()

    indir = os.path.abspath(args.indir)
    outdir = os.path.abspath(args.outdir)

    index = os.path.join(outdir, 'photosync.db')

    if not os.path.isdir(outdir):
        os.mkdir(outdir)

    if args.reindex:
        if os.path.isfile(index):
            os.remove(index)

    db = ps.DB(index)

    if args.reindex:
        for root, dirs, files in os.walk(outdir):
            index_images(db, root, files)

    if indir != '':
        for root, dirs, files in os.walk(indir):
            process_images(db, root, files, outdir)



if __name__ == "__main__":
    main()

