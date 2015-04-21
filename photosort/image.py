
import os
import sys
import re
import subprocess as sp
import tempfile

import exifread
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


def image_md5(filename, blocksize=2**20):
    m = hashlib.md5()
    #print('getting md5 of \"{}\"'.format(self.path))
    with open( filename, "rb" ) as f:
        while True:
            buf = f.read(blocksize)
            if not buf:
                break
            m.update( buf )
    return m.hexdigest()


class Image(object):


    def __init__(self, path):

        self.path = path
        self.name = os.path.basename(self.path)
        mat = re.match('(.*)\.(.*)', self.name)
        if not mat:
            raise RuntimeError('image name {} does not have an extension'.format(self.name))
        self.root = mat.group(1)
        self.ext = mat.group(2)

        if self.ext.lower() in image_raw_ext:
            # We have a raw file.  Extract the embedded image
            # and use this to grab the EXIF tags.
            with tempfile.TemporaryFile() as temp:
                proc_dcraw = sp.Popen ( [ 'dcraw', '-c', '-e', path ], stdout=temp, stderr=None, stdin=None )
                proc_dcraw.wait()
                temp.seek(0, 0)
                self.exif = exifread.process_file(temp)

        else:
            with open(self.path, 'rb') as f:
                self.exif = exifread.process_file(f)

        self._get_date()
        self.md5 = image_md5(self.path)
        self.uid = '{}{}{}:{}{}{}:{}'.format(self.year, self.month, self.day, self.hour, self.minute, self.second, self.name)
        #print('Image ctor {}'.format(self.path))
        #print('  name = {}'.format(self.name))
        #print('  root = {}, ext = {}'.format(self.root, self.ext))
        #print('  md5 = {}'.format(self.md5))
        #print('  {}-{}-{} {}:{}:{}'.format(self.year, self.month, self.day, self.hour, self.minute, self.second))
        #print('  UID = {}'.format(self.uid))
        #print('  exif:')
        #for k, v in self.exif.items():
        #    print ('    {} = {}'.format(k, v))


    def _get_date(self):
        pat = re.compile(r'.* DateTimeOriginal$')
        datepat = re.compile(r'^(\d*):(\d*):(\d*)\s+(\d*):(\d*):(\d*)\s*')
        
        self.year = None
        self.month = None
        self.day = None

        for k in self.exif.keys():
            v = self.exif[k]
            #print('"{}" = "{}"'.format(k, v))
            mat = pat.match(str(k))
            if mat:
                #print('key {} has DateTimeOriginal'.format(k))
                #print('val = {}'.format(str(v)))
                datemat = datepat.match(str(v))
                if datemat:
                    #print('val {} had date match'.format(v))
                    self.year = datemat.group(1)
                    self.month = datemat.group(2)
                    self.day = datemat.group(3)
                    self.hour = datemat.group(4)
                    self.minute = datemat.group(5)
                    self.second = datemat.group(6)
                    return

        if self.year is None:
            pat = re.compile(r'.* DateTime$')

            for k in self.exif.keys():
                v = self.exif[k]
                mat = pat.match(str(k))
                if mat:
                    #print('key {} has DateTime'.format(k))
                    datemat = datepat.match(str(v))
                    if datemat:
                        #print('val {} had date match'.format(v))
                        self.year = datemat.group(1)
                        self.month = datemat.group(2)
                        self.day = datemat.group(3)
                        self.hour = datemat.group(4)
                        self.minute = datemat.group(5)
                        self.second = datemat.group(6)
                        return

        if self.year is None:
            raise RuntimeError('file {} does not contain EXIF date information'.format(self.path))

        return



if __name__ == "__main__":

    path = sys.argv[1]
    img = Image(path)


