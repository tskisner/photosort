
import os
import sys
import shutil
import re
import argparse

import photosort as ps


def index_media(db, dir, files):
    # If files are manually moved to new directories (for example,
    # due to bad EXIF data), then we want to preserve those changes
    # when re-indexing.
    (temp, day) = os.path.split(dir)
    (temp, month) = os.path.split(temp)
    (temp, year) = os.path.split(temp)
    for f in files:
        infile = os.path.abspath( os.path.join(dir, f) )
        if ps.is_image(infile):
            print('indexing image {}'.format(infile))
            img = ps.Image(infile, year=year, month=month, day=day)
            db.insert(img)
        elif ps.is_video(infile):
            print('indexing video {}'.format(infile))
            vid = ps.Video(infile, year=year, month=month, day=day)
            db.insert(vid)


def import_media(db, indir, files, outroot):
    for f in files:
        mat = re.match('(.*)\.(.*)', f)
        if not mat:
            continue
        ext = mat.group(2)
        if (ext.lower() not in ps.image_ext) and (ext.lower() not in ps.video_ext):
            continue
        infile = os.path.abspath( os.path.join(indir, f) )
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
                # Uh-oh.  We have a file with the same name
                # and date as an existing image, but with a
                # DIFFERENT checksum!  Print a warning and
                # copy it to a new name.
                print('  WARNING: file with same name and date but different checksum found')
                print('  WARNING: copying to file name based on checksum to avoid overwrite.')
                outfile = os.path.abspath( os.path.join(daydir, obj.root) ) + '_DUP_' + chk + '.' + obj.ext
                if infile != outfile:
                    print('  copying to {}'.format(outfile))
                    shutil.copy2(infile, outfile)
                if obj.type == 'image':
                    newimg = ps.Image(outfile)
                    db.insert(newimg)
                elif obj.type == 'video':
                    newvid = ps.Video(outfile)
                    db.insert(newvid)
                else:
                    raise RuntimeError("should never get here...")

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

