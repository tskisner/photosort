
from __future__ import (absolute_import, division, print_function,
    unicode_literals)

import os


def album_append(adir, album, files):
    albumdir = os.path.join(os.path.abspath(adir), album)
    #print("albumdir = {}".format(albumdir))
    if not os.path.isdir(albumdir):
        os.mkdir(albumdir)
    for f in files:
        absfile = os.path.abspath(f)
        filename = os.path.basename(absfile)
        #print("absfile = {}".format(absfile))
        #print("filename = {}".format(filename))
        # we want the path relative to root...
        relfile = os.path.relpath(absfile, albumdir)
        #print("relfile = {}".format(relfile))
        linkpath = os.path.join(albumdir, filename)
        #print("linkpath = {}".format(linkpath))
        if not os.path.islink(linkpath):
            os.symlink(relfile, linkpath)
    return


def index_media(db, dir, files, file_time=False):
    for f in files:
        infile = os.path.abspath( os.path.join(dir, f) )
        if ps.is_image(infile):
            print('indexing image {}'.format(infile))
            img = ps.Image(infile, file_time)
            db.insert(img)
        elif ps.is_video(infile):
            print('indexing video {}'.format(infile))
            vid = ps.Video(infile, file_time)
            db.insert(vid)
        else:
            print('skipping non-media file {}'.format(infile))
    return


def import_media(db, indir, files, outroot, albumdir, file_time=False):
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
                obj = ps.Image(infile, file_time)
            elif ps.is_video(infile):
                obj = ps.Video(infile, file_time)
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
                if albumdir is not None:
                    # if we are making albums, take the parent directory and make it the album name
                    album = os.path.basename(indir)
                    safename = re.compile(r'[^0-9a-zA-Z-\.\/]')
                    album = safename.sub('_', album)
                    ps.album_append(albumdir, album, [outfile])
                print('  adding to DB')
                db.insert(obj)
            else:
                raise RuntimeError("file with same name, date and checksum prefix found which is not in DB.  You should rebuild the index.")
        else:
            print('  found in DB')
    return


def check_media(db, indir, files, outroot, missing, verbose=False):
    for f in files:
        mat = re.match('(.*)\.(.*)', f)
        if mat is None:
            continue
        ext = mat.group(2)
        if (ext.lower() not in ps.image_ext) and (ext.lower() not in ps.video_ext):
            continue
        infile = os.path.abspath( os.path.join(indir, f) )

        chk = ps.file_md5(infile)
        rname, chkshort = ps.file_rootname(infile)

        if (chkshort != "") and (chkshort != chk[0:4]):
            print('{} has short checksum {} (not {}) and may be corrupted'.format(infile, chk[0:4], chkshort))

        if (not db.query_md5(chk)):
            obj = None
            if ps.is_image(infile):
                obj = ps.Image(infile)
            elif ps.is_video(infile):
                obj = ps.Video(infile)
            else:
                raise RuntimeError("Should never get here...")
            print('{} not in DB'.format(infile))
            missing += os.stat(infile).st_size

            yeardir = os.path.join(outroot, obj.year)
            monthdir = os.path.join(yeardir, obj.month)
            daydir = os.path.join(monthdir, obj.day)

            result = db.query(obj.uid)

            if result is not None:
                raise RuntimeError("file with same name, date and checksum prefix found which is not in DB.  You should rebuild the index.")
        else:
            if verbose:
                print('found {}'.format(infile))
    return missing
