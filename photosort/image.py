
import os
import sys
import re
import subprocess as sp
import tempfile

import exifread


class Image(object):

    def __init__(self, path):
        
        self.rawext = [
            '3fr', 'ari',
            'arw', 'bay', 'crw', 'cr2', 'cap', 'dcs',
            'dcr', 'dng', 'drf', 'eip', 'erf', 'fff', 
            'iiq', 'k25', 'kdc', 'mdc', 'mef', 'mos',
            'mrw', 'nef', 'nrw', 'obm', 'orf', 'pef',
            'ptx', 'pxn', 'r3d', 'raf', 'raw', 'rwl',
            'rw2', 'rwz', 'sr2', 'srf', 'srw', 'x3f'
        ]

        self.path = path
        self.name = os.path.basename(self.path)
        mat = re.match('(.*)\.(.*)', self.name)
        if not mat:
            raise RuntimeError('image name {} does not have an extension'.format(self.name))
        self.root = mat.group(1)
        self.ext = mat.group(2)

        if self.ext in self.rawext:
            # We have a raw file.  Extract the embedded image
            # and use this to grab the EXIF tags.
            with tempfile.TemporaryFile() as temp:
                proc_dcraw = sp.Popen ( [ 'dcraw', '-c', '-e', path ], stdout=temp, stderr=None, stdin=None )
                proc_dcraw.wait()
                temp.seek(0, 0)
                self.tags = exifread.process_file(temp)

        else:
            with open(self.path, 'rb') as f:
                self.tags = exifread.process_file(f)

        self._get_date()

        print('Image ctor {}'.format(self.path))
        print('  name = {}'.format(self.name))
        print('  root = {}, ext = {}'.format(self.root, self.ext))
        print('  year = {}, month = {}, day = {}'.format(self.year, self.month, self.day))
        print('  exif:')
        for k, v in self.tags.items():
            print ('    {} = {}'.format(k, v))

    def _get_date(self):
        pat = re.compile(r'.* DateTimeOriginal$')
        datepat = re.compile(r'^(\d*):(\d*):(\d*)\s+.*')
        
        self.year = None
        self.month = None
        self.day = None

        for k in self.tags.keys():
            v = self.tags[k]
            print('"{}" = "{}"'.format(k, v))
            mat = pat.match(k)
            if mat:
                print('key {} has DateTimeOriginal'.format(k))
                datemat = datepat.match(v)
                if datemat:
                    print('val {} had date match'.format(v))
                    self.year = datemat.group(1)
                    self.month = datemat.group(2)
                    self.day = datemat.group(3)
                    return

        if self.year is None:
            pat = re.compile(r'.* DateTime$')

            for k in self.tags.keys():
                v = self.tags[k]
                mat = pat.match(k)
                if mat:
                    print('key {} has DateTime'.format(k))
                    datemat = datepat.match(v)
                    if datemat:
                        print('val {} had date match'.format(v))
                        self.year = datemat.group(1)
                        self.month = datemat.group(2)
                        self.day = datemat.group(3)
                        return

        if self.year is None:
            raise RuntimeError('file {} does not contain EXIF date information'.format(self.path))

        return


if __name__ == "__main__":

    path = sys.argv[1]
    img = Image(path)


