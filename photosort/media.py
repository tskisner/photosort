
import os
import sys
import re
import subprocess as sp
import json
import tempfile
import datetime

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


def is_image(filename):
    base = os.path.basename(filename)
    mat = re.match('(.*)\.(.*)', base)
    if not mat:
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
    if not mat:
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
            if mat:
                ret['year'] = mat.group(1)
                ret['month'] = mat.group(2)
                ret['day'] = mat.group(3)
                ret['hour'] = mat.group(4)
                ret['minute'] = mat.group(5)
                ret['second'] = mat.group(6)
                #print("file_date:  using key {}".format(p))
                break
    if ret['year'] is None:
        # We have no metadata date information.  Just use the file
        # modification time (not ideal).
        t = os.path.getmtime(filename)
        tstr = str(datetime.datetime.fromtimestamp(t))
        datepat = re.compile(r'^(\d*)-(\d*)-(\d*)\s+(\d*):(\d*):(\d*)\s*')
        mat = datepat.match(tstr)
        if mat:
            ret['year'] = mat.group(1)
            ret['month'] = mat.group(2)
            ret['day'] = mat.group(3)
            ret['hour'] = mat.group(4)
            ret['minute'] = mat.group(5)
            ret['second'] = str(int(float(mat.group(6))))
        else:
            raise RuntimeError('cannot get date/time from metadata or filesystem for {}', filename)
    return ret
    

class Image(object):


    def __init__(self, path, year=None, month=None, day=None):
        self.type = 'image'
        self.path = path
        self.name = os.path.basename(self.path)
        mat = re.match('(.*)\.(.*)', self.name)
        if not mat:
            raise RuntimeError('file {} does not have an extension'.format(self.path))
        self.root = mat.group(1)
        self.ext = mat.group(2)

        if self.ext.lower() in image_raw_ext:
            # We have a raw file.  Extract the embedded image
            # and use this to grab the EXIF tags.
            tempname = ''
            with tempfile.NamedTemporaryFile(delete=False) as temp:
                tempname = temp.name
                proc_dcraw = sp.Popen ( [ 'dcraw', '-c', '-e', self.path ], stdout=temp, stderr=None, stdin=None )
                proc_dcraw.wait()
            self.meta = file_json(tempname)
            os.unlink(tempname)
        elif self.ext.lower() in image_nonraw_ext:
            self.meta = file_json(self.path)
        else:
            raise RuntimeError('file {} is not an image'.format(self.path))

        metadate = file_date(self.path, self.meta, image_date_meta)

        if year is None:
            self.year = metadate['year']
        else:
            self.year = year
        if month is None:
            self.month = metadate['month']
        else:
            self.month = month
        if day is None:
            self.day = metadate['day']
            self.hour = metadate['hour']
            self.minute = metadate['minute']
            self.second = metadate['second']
        else:
            # if we are overriding the day, the time
            # is clearly wrong too.
            self.day = day
            self.hour = '00'
            self.minute = '00'
            self.second = '00'

        self.md5 = file_md5(self.path)
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


    def __init__(self, path, year=None, month=None, day=None):
        self.type = 'video'
        self.path = path
        self.name = os.path.basename(self.path)
        mat = re.match('(.*)\.(.*)', self.name)
        if not mat:
            raise RuntimeError('file {} does not have an extension'.format(self.path))
        self.root = mat.group(1)
        self.ext = mat.group(2)

        if self.ext.lower() in video_ext:
            self.meta = file_json(self.path)
        else:
            raise RuntimeError('file {} is not a video'.format(self.path))

        metadate = file_date(self.path, self.meta, video_date_meta)

        if year is None:
            self.year = metadate['year']
        else:
            self.year = year
        if month is None:
            self.month = metadate['month']
        else:
            self.month = month
        if day is None:
            self.day = metadate['day']
            self.hour = metadate['hour']
            self.minute = metadate['minute']
            self.second = metadate['second']
        else:
            # if we are overriding the day, the time
            # is clearly wrong too.
            self.day = day
            self.hour = '00'
            self.minute = '00'
            self.second = '00'

        self.md5 = file_md5(self.path)
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
    #img = Image(path)
    vid = Video(path)

