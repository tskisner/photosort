
import os
import sys
import shutil
import re
import argparse

import photosort as ps


def index_media(db, dir, files):
    for f in files:
        infile = os.path.abspath( os.path.join(dir, f) )
        if ps.is_image(infile):
            print('indexing image {}'.format(infile))
            img = ps.Image(infile)
            db.insert(img)
        elif ps.is_video(infile):
            print('indexing video {}'.format(infile))
            vid = ps.Video(infile)
            db.insert(vid)
        else:
            print('skipping non-media file {}'.format(infile))


def import_media(db, indir, files, outroot):
    for f in files:
        mat = re.match('(.*)\.(.*)', f)
        if mat is None:
            print('skipping non-media file {}'.format(infile))
            continue
        ext = mat.group(2)
        infile = os.path.abspath( os.path.join(indir, f) )
        if (ext.lower() not in ps.image_ext) and (ext.lower() not in ps.video_ext):
            print('skipping non-media file {}'.format(infile))
            continue
        album = os.path.basename(indir)
        safename = re.compile(r'[^0-9a-zA-Z-\.\/]')
        album = safename.sub('_', album)

        chk = ps.file_md5(infile)
        print('checking {}'.format(infile))
        if (not db.query_md5(chk)):
            obj = None
            if ps.is_image(infile):
                obj = ps.Image(infile)
            elif ps.is_video(infile):
                obj = ps.Video(infile)
            else:
                raise RuntimeError("Should never get here...")
            yeardir = os.path.join(outroot, obj.year)
            monthdir = os.path.join(yeardir, obj.month)
            daydir = os.path.join(monthdir, obj.day)
            if not os.path.isdir(outroot):
                os.mkdir(outroot)
            if not os.path.isdir(yeardir):
                os.mkdir(yeardir)
            if not os.path.isdir(monthdir):
                os.mkdir(monthdir)
            if not os.path.isdir(daydir):
                os.mkdir(daydir)

            result = db.query(obj.uid)
            if result is None:
                outfile = os.path.abspath( os.path.join(daydir, obj.name) )
                if infile != outfile:
                    print('  copying to {}'.format(outfile))
                    shutil.copy2(infile, outfile)
                ps.album_append(outroot, album, [outfile])
                print('  adding to DB')
                db.insert(obj)
            else:
                raise RuntimeError("file with same name, date and checksum prefix found which is not in DB.  You should rebuild the index.")
        else:
            print('  found in DB')


def main():
    parser = argparse.ArgumentParser( description='Organize photos and videos by metadata.' )
    parser.add_argument( '--indir', required=False, default='', help='input directory' )
    parser.add_argument( '--outdir', required=True, default='', help='output directory' )
    parser.add_argument( '--reindex', required=False, default=False, action='store_true', help='force rebuild of index' )
    args = parser.parse_args()

    indir = os.path.abspath(args.indir)
    outdir = os.path.abspath(args.outdir)

    index = os.path.join(outdir, 'photosync.db')

    if not os.path.isdir(outdir):
        os.mkdir(outdir)

    albumdir = os.path.join(outdir, 'albums')
    if not os.path.isdir(albumdir):
        os.mkdir(albumdir)

    if args.reindex:
        if os.path.isfile(index):
            os.remove(index)

    db = ps.DB(index)

    if args.reindex:
        for root, dirs, files in os.walk(outdir):
            index_media(db, root, files)

    if args.indir != '':
        for root, dirs, files in os.walk(indir):
            import_media(db, root, files, outdir)



if __name__ == "__main__":
    main()

