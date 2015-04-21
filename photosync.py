
import os
import sys
import shutil
import re
import argparse

import photosort as ps


def process_images(db, indir, files, tags, outroot):
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
            print('  adding to DB')
            img = ps.Image(infile)
            img.tags = tags
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
            outfile = os.path.abspath( os.path.join(daydir, img.name) )
            tagfile = outfile + '.tags'
            if infile != outfile:
                print('  copying to {}'.format(outfile))
                shutil.copy2(infile, outfile)
                with open(tagfile, 'w') as tfile:
                    tagstr = ','.join(tags) + '\n'
                    tfile.write(tagstr)
            db.insert(img)
        else:
            print('  found in DB')


def main():
    parser = argparse.ArgumentParser( description='Organize photos by EXIF data.' )
    parser.add_argument( '--indir', required=True, default='.', help='input directory' )
    parser.add_argument( '--outdir', required=True, default='.', help='output directory' )
    parser.add_argument( '--reindex', required=False, help='force rebuild of index' )
    parser.add_argument( '--tags', required=False, help='comma-separated list of tags to apply' )
    args = parser.parse_args()

    indir = os.path.abspath(args.indir)
    outdir = os.path.abspath(args.outdir)

    tags = []
    if args.tags is not None:
        tags = args.tags.split(',')

    index = os.path.join(outdir, 'photosync.db')

    if not os.path.isdir(outdir):
        os.mkdir(outdir)

    if args.reindex:
        if os.path.isfile(index):
            os.remove(index)

    db = ps.DB(index)

    if args.reindex:
        for root, dirs, files in os.walk(outdir):
            process_images(db, root, files, tags, outdir)

    for root, dirs, files in os.walk(indir):
        process_images(db, root, files, tags, outdir)



if __name__ == "__main__":
    main()

