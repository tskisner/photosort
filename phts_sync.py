
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
    return


def import_media(db, indir, files, outroot, mkalbums):
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

        # compute MD5 sum
        chk = ps.file_md5(infile)

        # does this checksum already exist in the database?
        print('checking {}'.format(infile))
        if (not db.query_md5(chk)):

            # load the object depending on type
            obj = None
            if ps.is_image(infile):
                obj = ps.Image(infile)
            elif ps.is_video(infile):
                obj = ps.Video(infile)
            else:
                raise RuntimeError("Should never get here...")

            # get the date as a tuple
            date = (obj.year, obj.month, obj.day, obj.hour, obj.minute, obj.second)

            # does this object have a reasonable date stamp?
            dategood = ps.good_date(date)

            # default is to put the file in the broken dir
            daydir = os.path.join(outroot, "broken")

            if dategood:
                # if the date is reasonable, make the day directory
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

            # does an object with this checksum and filename exist in DB (it shouldn't yet)?
            result = db.query(obj.uid)
            if result is None:
                outfile = os.path.abspath( os.path.join(daydir, obj.name) )
                if infile != outfile:
                    print('  copying to {}'.format(outfile))
                    shutil.copy2(infile, outfile)
                    # if the date stamp on the file is good, update modification
                    # time to reflect that.
                    if dategood:
                        ps.file_setdate(outfile, date)
                if mkalbums:
                    # if we are making albums, take the parent directory and make it the album name
                    album = os.path.basename(indir)
                    safename = re.compile(r'[^0-9a-zA-Z-\.\/]')
                    album = safename.sub('_', album)
                    ps.album_append(outroot, album, [outfile])
                print('  adding to DB')
                db.insert(obj)
            else:
                raise RuntimeError("file with same name, date and checksum prefix found which is not in DB.  You should rebuild the index.")
        else:
            print('  found in DB')
    return


def main():
    parser = argparse.ArgumentParser( description='Organize photos and videos by metadata.' )
    parser.add_argument( '--indir', required=False, default='', help='input directory' )
    parser.add_argument( '--outdir', required=True, default='', help='output directory' )
    parser.add_argument( '--albums', required=False, default=False, action='store_true', help='create new albums based on input directories' )
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

    brokendir = os.path.join(outdir, 'broken')
    if not os.path.isdir(brokendir):
        os.mkdir(brokendir)

    if args.reindex:
        if os.path.isfile(index):
            os.remove(index)

    db = ps.DB(index)

    if args.reindex:
        exclude = []
        exclude.append('albums')
        for root, dirs, files in os.walk(outdir, topdown=True):
            dirs[:] = [d for d in dirs if d not in exclude]
            index_media(db, root, files)

    if args.indir != '':
        for root, dirs, files in os.walk(indir):
            import_media(db, root, files, outdir, args.albums)



if __name__ == "__main__":
    main()

