
import os
import sys
import shutil
import re
import argparse

import photosort as ps


def check_media(db, indir, files, outroot, verbose=False):
    for f in files:
        mat = re.match('(.*)\.(.*)', f)
        if mat is None:
            continue
        ext = mat.group(2)
        if (ext.lower() not in ps.image_ext) and (ext.lower() not in ps.video_ext):
            continue
        infile = os.path.abspath( os.path.join(indir, f) )

        chk = ps.file_md5(infile)

        if (not db.query_md5(chk)):
            obj = None
            if ps.is_image(infile):
                obj = ps.Image(infile)
            elif ps.is_video(infile):
                obj = ps.Video(infile)
            else:
                raise RuntimeError("Should never get here...")
            print('{} not in DB'.format(infile))

            yeardir = os.path.join(outroot, obj.year)
            monthdir = os.path.join(yeardir, obj.month)
            daydir = os.path.join(monthdir, obj.day)

            result = db.query(obj.uid)

            if result is not None:
                raise RuntimeError("file with same name, date and checksum prefix found which is not in DB.  You should rebuild the index.")
        else:
            if verbose:
                print('found {}'.format(infile))
    return


def main():
    parser = argparse.ArgumentParser( description='Verify photos and videos by metadata.' )
    parser.add_argument( '--original', required=False, default='', help='original input directory' )
    parser.add_argument( '--outdir', required=True, default='', help='output directory' )
    parser.add_argument( '--verbose', required=False, default=False, action='store_true', help='verbose output' )

    args = parser.parse_args()

    indir = os.path.abspath(args.original)
    outdir = os.path.abspath(args.outdir)

    index = os.path.join(outdir, 'photosync.db')

    if not os.path.isdir(indir):
        raise RuntimeError('original directory does not exist')

    if not os.path.isdir(outdir):
        raise RuntimeError('output directory does not exist')

    db = ps.DB(index)

    for root, dirs, files in os.walk(indir):
        check_media(db, root, files, outdir, verbose=args.verbose)



if __name__ == "__main__":
    main()

