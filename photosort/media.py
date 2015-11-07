
import os
import sys
import re
import subprocess as sp
import json
import tempfile
import datetime
import time

import hashlib


image_nonraw_ext = [
    'jpg', 'jpeg', 'tif', 'tiff'
]

image_raw_ext = [
    '3fr', 'ari',
    'arw', 'bay', 'crw', 'cr2', 'cap', 'dcs',
    'dcr', 'dng', 'drf', 'eip', 'erf', 'fff', 
    'iiq', 'k25', 'kdc', 'mdc', 'mef', 'mos',
    'mrw', 'nef', 'nrw', 'obm', 'orf', 'pef',
    'ptx', 'pxn', 'r3d', 'raf', 'raw', 'rwl',
    'rw2', 'rwz', 'sr2', 'srf', 'srw', 'x3f'
]

image_ext = image_nonraw_ext + image_raw_ext

video_ext = [
    'mov', 'qt', 'avi', 'mp4', 'mpg', 'dv',
    'flv', 'mpeg', 'm2v', 'swf', 'wma', 'wmv',
    'm2ts', 'mts', 'm2t', 'ts',
    'm4a', 'm4b', 'm4p', 'm4v'
]

image_date_meta = [
    'DateTimeOriginal', 'DateTime'
]

video_date_meta = [
    'DateTimeOriginal', 'CreationDate', 'CreateDate'
]


def file_md5(filename, blocksize=2**20):
    m = hashlib.md5()
    #print('getting md5 of \"{}\"'.format(self.path))
    with open( filename, "rb" ) as f:
        while True:
            buf = f.read(blocksize)
            if not buf:
                break
            m.update( buf )
    return m.hexdigest()


def file_json(filename):
    exif = sp.check_output ( [ 'exiftool', '-j', '-sort', filename ], universal_newlines=True )
    return json.loads(exif.rstrip('\r\n'))[0]


def file_setdate(filename, date):
    datestr = "{:04d}:{:02d}:{:02d} {:02d}:{:02d}:{:02d}".format(int(date[0]), int(date[1]), int(date[2]), int(date[3]), int(date[4]), int(date[5]))
    st = time.strptime(datestr, "%Y:%m:%d %H:%M:%S")
    systime = time.mktime(st)
    os.utime(filename, (systime, systime))
    return


def file_setmetadate(filename, date):
    comstr = "File dates corrected by photosort on {}".format(datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S'))
    datestr = "{:04d}:{:02d}:{:02d} {:02d}:{:02d}:{:02d}".format(int(date[0]), int(date[1]), int(date[2]), int(date[3]), int(date[4]), int(date[5]))
    code = sp.check_call ( [ 'exiftool', '-AllDates={}'.format(datestr), '-overwrite_original', '-comment={}'.format(comstr), filename ] )
    return


def good_date(date):
    iyear = int(date[0])
    imonth = int(date[1])
    iday = int(date[2])
    now = datetime.datetime.now()
    nowyear = int(datetime.datetime.strftime(now, '%Y'))
    # does the year make sense?
    if iyear == 0:
        return False
    if iyear > nowyear:
        return False
    if (imonth < 1) or (imonth > 12):
        return False
    if (iday < 1) or (iday > 31):
        return False
    return True


def file_ckname(filename, md5):
    mat = re.match(r'(.*)\.(.*)', filename)
    if mat is None:
        raise RuntimeError('file name {} does not have an extension'.format(filename))
    root = mat.group(1)
    ext = mat.group(2)
    ckmat = re.match(r'(.*)_ck([a-z0-9]{4})$', root)
    full = filename
    if ckmat is None:
        full = "{}_ck{}.{}".format(root, md5[0:4], ext)
    else:
        origroot = ckmat.group(1)
        ck = ckmat.group(2)
        if ck != md5[0:4]:
            raise RuntimeError('file name {} does not match checksum({})'.format(filename, md5))
    return full


def file_rootname(full):
    mat = re.match(r'(.*)\.(.*)', full)
    if mat is None:
        raise RuntimeError('file name {} does not have an extension'.format(full))
    root = mat.group(1)
    ext = mat.group(2)
    ckmat = re.match(r'(.*)_ck[a-z0-9]{4}$', root)
    filename = full
    if ckmat is not None:
        origroot = ckmat.group(1)
        filename = "{}.{}".format(origroot, ext)
    return filename


def is_image(filename):
    base = os.path.basename(filename)
    mat = re.match('(.*)\.(.*)', base)
    if mat is None:
        raise RuntimeError('file name {} does not have an extension'.format(filename))
    root = mat.group(1)
    ext = mat.group(2)
    if ext.lower() in image_ext:
        return True
    else:
        return False


def is_video(filename):
    base = os.path.basename(filename)
    mat = re.match('(.*)\.(.*)', base)
    if mat is None:
        raise RuntimeError('file name {} does not have an extension'.format(filename))
    root = mat.group(1)
    ext = mat.group(2)
    if ext.lower() in video_ext:
        return True
    else:
        return False


def file_date(filename, meta, prior):
    ret = {}
    ret['year'] = None
    ret['month'] = None
    ret['day'] = None
    ret['hour'] = None
    ret['minute'] = None
    ret['second'] = None
    datepat = re.compile(r'^(\d\d\d\d):(\d\d):(\d\d)\s+(\d\d):(\d\d):(\d\d).*')
    for p in prior:
        if p in meta.keys():
            v = meta[p]
            mat = datepat.match(str(v))
            if mat is not None:
                ret['year'] = mat.group(1)
                ret['month'] = mat.group(2)
                ret['day'] = mat.group(3)
                ret['hour'] = mat.group(4)
                ret['minute'] = mat.group(5)
                ret['second'] = mat.group(6)
                #print("file_date:  using key {}".format(p))
                break
    if ret['year'] is None:
        # We have no metadata date information.  Since timestamps
        # are completely unreliable, we set this file time to all zero,
        # so that it will be flagged as "broken" for manual intervention.
        ret['year'] = '0000'
        ret['month'] = '00'
        ret['day'] = '00'
        ret['hour'] = '00'
        ret['minute'] = '00'
        ret['second'] = '00'
    return ret


def album_append(root, album, files):
    absroot = os.path.abspath(root)
    #print("absroot = {}".format(absroot))
    albumdir = os.path.join(absroot, 'albums', album)
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


class Image(object):

    def __init__(self, path):
        self.type = 'image'
        self.path = path
        bname = os.path.basename(self.path)
        mat = re.match('(.*)\.(.*)', bname)
        if not mat:
            raise RuntimeError('file {} does not have an extension'.format(self.path))
        self.root = mat.group(1)
        self.ext = mat.group(2)

        if (self.ext.lower() in image_raw_ext) or (self.ext.lower() in image_nonraw_ext):
            self.meta = file_json(self.path)
        else:
            raise RuntimeError('file {} is not an image'.format(self.path))

        metadate = file_date(self.path, self.meta, image_date_meta)

        self.year = metadate['year']
        self.month = metadate['month']
        self.day = metadate['day']
        self.hour = metadate['hour']
        self.minute = metadate['minute']
        self.second = metadate['second']

        self.md5 = file_md5(self.path)
        rname = file_rootname(bname)
        self.name = file_ckname(rname, self.md5)
        self.uid = '{}{}{}:{}{}{}:{}'.format(self.year, self.month, self.day, self.hour, self.minute, self.second, self.name)
        #print('Image ctor {}'.format(self.path))
        #print('  name = {}'.format(self.name))
        #print('  root = {}, ext = {}'.format(self.root, self.ext))
        #print('  md5 = {}'.format(self.md5))
        #print('  {}-{}-{} {}:{}:{}'.format(self.year, self.month, self.day, self.hour, self.minute, self.second))
        #print('  UID = {}'.format(self.uid))
        #print('  exif:')
        #for k, v in self.meta.items():
        #    print ('    {} = {}'.format(k, v))


class Video(object):


    def __init__(self, path):
        self.type = 'video'
        self.path = path
        bname = os.path.basename(self.path)
        mat = re.match('(.*)\.(.*)', bname)
        if not mat:
            raise RuntimeError('file {} does not have an extension'.format(self.path))
        self.root = mat.group(1)
        self.ext = mat.group(2)

        if self.ext.lower() in video_ext:
            self.meta = file_json(self.path)
        else:
            raise RuntimeError('file {} is not a video'.format(self.path))

        metadate = file_date(self.path, self.meta, video_date_meta)

        self.year = metadate['year']
        self.month = metadate['month']
        self.day = metadate['day']
        self.hour = metadate['hour']
        self.minute = metadate['minute']
        self.second = metadate['second']

        self.md5 = file_md5(self.path)
        rname = file_rootname(bname)
        self.name = file_ckname(rname, self.md5)
        self.uid = '{}{}{}:{}{}{}:{}'.format(self.year, self.month, self.day, self.hour, self.minute, self.second, self.name)
        #print('Video ctor {}'.format(self.path))
        #print('  name = {}'.format(self.name))
        #print('  root = {}, ext = {}'.format(self.root, self.ext))
        #print('  md5 = {}'.format(self.md5))
        #print('  {}-{}-{} {}:{}:{}'.format(self.year, self.month, self.day, self.hour, self.minute, self.second))
        #print('  UID = {}'.format(self.uid))
        #print('  exif:')
        #for k, v in self.meta.items():
        #    print ('    {} = {}'.format(k, v))





if __name__ == "__main__":

    path = sys.argv[1]
    img = Image(path)
    #vid = Video(path)
    print(img.path)
    print(img.md5)
    full = file_ckname(img.path, img.md5)
    print(full)
    full2 = file_ckname(full, img.md5)
    print(full2)
    stripped = file_rootname(full2)
    print(stripped)
    stripped2 = file_rootname(stripped)
    print(stripped2)
