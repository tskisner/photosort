
from __future__ import (absolute_import, division, print_function,
    unicode_literals)

import os
import sys
import re
import subprocess as sp
import json
import tempfile
import datetime
import time
import shutil

import hashlib


image_nonraw_ext = [
    "jpg", "jpeg", "tif", "tiff"
]

image_raw_ext = [
    "3fr", "ari",
    "arw", "bay", "crw", "cr2", "cap", "dcs",
    "dcr", "dng", "drf", "eip", "erf", "fff",
    "iiq", "k25", "kdc", "mdc", "mef", "mos",
    "mrw", "nef", "nrw", "obm", "orf", "pef",
    "ptx", "pxn", "r3d", "raf", "raw", "rwl",
    "rw2", "rwz", "sr2", "srf", "srw", "x3f"
]

image_ext = image_nonraw_ext + image_raw_ext

video_ext = [
    "mov", "qt", "avi", "mp4", "mpg", "dv",
    "flv", "mpeg", "m2v", "swf", "wma", "wmv",
    "m2ts", "mts", "m2t", "ts",
    "m4a", "m4b", "m4p", "m4v"
]

image_date_meta = [
    "DateTimeOriginal", "DateTime"
]

video_date_meta = [
    "DateTimeOriginal", "CreationDate", "CreateDate"
]


def file_md5(filename, blocksize=2**20):
    m = hashlib.md5()
    #print("getting md5 of \"{}\"".format(self.path))
    with open( filename, "rb" ) as f:
        while True:
            buf = f.read(blocksize)
            if not buf:
                break
            m.update( buf )
    return m.hexdigest()


def file_json(filename):
    exif = sp.check_output ( [ "exiftool", "-j", "-sort", filename ],
        universal_newlines=True )
    return json.loads(exif.rstrip("\r\n"))[0]


def file_setdate(filename, date):
    # datestr = "{:04d}:{:02d}:{:02d} {:02d}:{:02d}:{:02d}".format(int(date[0]),
    #     int(date[1]), int(date[2]), int(date[3]), int(date[4]), int(date[5]))
    # st = time.strptime(datestr, "%Y:%m:%d %H:%M:%S")
    # systime = time.mktime(st)
    # os.utime(filename, times=(systime, systime))
    datestr = "{:04d}{:02d}{:02d}{:02d}{:02d}.{:02d}".format(int(date[0]),
        int(date[1]), int(date[2]), int(date[3]), int(date[4]), int(date[5]))
    sp.check_call(["touch", "-t", datestr, filename])
    return


def file_setmetadate(filename, date):
    comstr = "File dates corrected by photosort on {}"\
        .format(datetime.datetime.strftime(datetime.datetime.now(),
        "%Y-%m-%d %H:%M:%S"))
    datestr = "{:04d}:{:02d}:{:02d} {:02d}:{:02d}:{:02d}".format(int(date[0]),
        int(date[1]), int(date[2]), int(date[3]), int(date[4]), int(date[5]))
    code = sp.check_call ( [ "exiftool", "-AllDates={}".format(datestr),
        "-overwrite_original", "-comment={}".format(comstr), filename ] )
    return


def good_date(date):
    iyear = int(date[0])
    imonth = int(date[1])
    iday = int(date[2])
    now = datetime.datetime.now()
    nowyear = int(datetime.datetime.strftime(now, "%Y"))
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
    mat = re.match(r"(.*)\.(.*)", filename)
    if mat is None:
        raise RuntimeError("file name {} does not have an extension"\
            .format(filename))
    root = mat.group(1)
    ext = mat.group(2)
    ckmat = re.match(r"(.*)_ck([a-z0-9]{4})$", root)
    full = filename
    if ckmat is None:
        full = "{}_ck{}.{}".format(root, md5[0:4], ext)
    else:
        origroot = ckmat.group(1)
        ck = ckmat.group(2)
        if ck != md5[0:4]:
            raise RuntimeError("file name {} does not match checksum({})"\
                .format(filename, md5))
    return full


def file_rootname(full):
    mat = re.match(r"(.*)\.(.*)", full)
    if mat is None:
        raise RuntimeError("file name {} does not have an extension"\
            .format(full))
    root = mat.group(1)
    ext = mat.group(2)
    ckmat = re.match(r"(.*)_ck([a-z0-9]{4})$", root)
    filename = full
    ckshort = ""
    if ckmat is not None:
        origroot = ckmat.group(1)
        filename = "{}.{}".format(origroot, ext)
        ckshort = ckmat.group(2)
    return filename, ckshort


def is_image(filename):
    base = os.path.basename(filename)
    mat = re.match("(.*)\.(.*)", base)
    if mat is None:
        raise RuntimeError("file name {} does not have an extension"\
            .format(filename))
    root = mat.group(1)
    ext = mat.group(2)
    if ext.lower() in image_ext:
        return True
    else:
        return False


def is_video(filename):
    base = os.path.basename(filename)
    mat = re.match("(.*)\.(.*)", base)
    if mat is None:
        raise RuntimeError("file name {} does not have an extension"\
            .format(filename))
    root = mat.group(1)
    ext = mat.group(2)
    if ext.lower() in video_ext:
        return True
    else:
        return False


def file_date(filename, meta, prior, file_time=False):
    ret = {}
    ret["year"] = None
    ret["month"] = None
    ret["day"] = None
    ret["hour"] = None
    ret["minute"] = None
    ret["second"] = None
    datepat = re.compile(r"^(\d\d\d\d):(\d\d):(\d\d)\s+(\d\d):(\d\d):(\d\d).*")
    for p in prior:
        if p in meta.keys():
            v = meta[p]
            mat = datepat.match(str(v))
            if mat is not None:
                ret["year"] = mat.group(1)
                ret["month"] = mat.group(2)
                ret["day"] = mat.group(3)
                ret["hour"] = mat.group(4)
                ret["minute"] = mat.group(5)
                ret["second"] = mat.group(6)
                #print("file_date:  using key {}".format(p))
                break
    if ret["year"] is None:
        # We have no metadata date information.  Since timestamps
        # are completely unreliable, we set this file time to all zero,
        # so that it will be flagged as "broken" for manual intervention.
        ret["year"] = "0000"
        ret["month"] = "00"
        ret["day"] = "00"
        ret["hour"] = "00"
        ret["minute"] = "00"
        ret["second"] = "00"
        if file_time:
            # We explicity want to use the file date stamp...
            t = os.path.getmtime(filename)
            tstr = str(datetime.datetime.fromtimestamp(t))
            datepat = re.compile(r"^(\d*)-(\d*)-(\d*)\s+(\d*):(\d*):(\d*)\s*")
            datemat = datepat.match(tstr)
            if datemat:
                ret["year"] = datemat.group(1)
                ret["month"] = datemat.group(2)
                ret["day"] = datemat.group(3)
                ret["hour"] = datemat.group(4)
                ret["minute"] = datemat.group(5)
                ret["second"] = str(int(float(datemat.group(6))))
    return ret


def is_subdir(path, directory):
    path = os.path.realpath(path)
    directory = os.path.realpath(directory)
    relative = os.path.relpath(path, directory)
    if relative.startswith(os.pardir):
        return False
    else:
        return True


class Image(object):

    def __init__(self, path, file_time=False):
        self.type = "image"
        self.path = path
        bname = os.path.basename(self.path)
        mat = re.match("(.*)\.(.*)", bname)
        if mat is None:
            raise RuntimeError(\
                "file {} does not have an extension".format(self.path))
        self.root = mat.group(1)
        self.ext = mat.group(2)

        if (self.ext.lower() in image_raw_ext) or (self.ext.lower() \
            in image_nonraw_ext):
            self.meta = file_json(self.path)
        else:
            raise RuntimeError("file {} is not an image".format(self.path))

        metadate = file_date(self.path, self.meta, image_date_meta,
            file_time=file_time)

        self.year = metadate["year"]
        self.month = metadate["month"]
        self.day = metadate["day"]
        self.hour = metadate["hour"]
        self.minute = metadate["minute"]
        self.second = metadate["second"]

        self.md5 = file_md5(self.path)
        rname, ckshort = file_rootname(bname)
        self.name = file_ckname(rname, self.md5)
        self.uid = "{}{}{}:{}{}{}:{}".format(self.year, self.month, self.day,
            self.hour, self.minute, self.second, self.name)
        #print("Image ctor {}".format(self.path))
        #print("  name = {}".format(self.name))
        #print("  root = {}, ext = {}".format(self.root, self.ext))
        #print("  md5 = {}".format(self.md5))
        #print("  {}-{}-{} {}:{}:{}".format(self.year, self.month, self.day,
        #    self.hour, self.minute, self.second))
        #print("  UID = {}".format(self.uid))
        #print("  exif:")
        #for k, v in self.meta.items():
        #    print ("    {} = {}".format(k, v))

    def export(self, path, resolution="FULL"):
        qual_opts = ["-quality", "95"]
        res_opts = []
        if resolution == "MED":
            res_opts.append("-scale")
            res_opts.append("50%")
        elif resolution == "LOW":
            res_opts.append("-scale")
            res_opts.append("25%")
        com_meta = ["exiftool", "-q", "-overwrite_original", "-TagsFromFile",
            self.path, path]

        if self.ext.lower() in image_raw_ext:
            # We have a raw file.  Extract with dcraw and
            # pipe to convert.  Resize before JPEG conversion.
            # Then copy metadata with exiftool.
            com_convert = ["convert"]
            com_convert.extend(res_opts)
            com_convert.extend(qual_opts)
            com_convert.append("pnm:-")
            com_convert.append(path)
            proc_dcraw = sp.Popen([ "dcraw", "-c", self.path ],
                stdout=sp.PIPE, stderr=None, stdin=None)
            proc_convert = sp.Popen(com_convert, stdin=proc_dcraw.stdout,
                stdout=None, stderr=None)
            output = proc_convert.communicate()[0]
            proc_convert.wait()
            proc_meta = sp.Popen(com_meta, stdout=None, stderr=None, stdin=None)
            proc_meta.wait()

        else:
            if (resolution == "FULL") and (self.ext.lower() == "jpg"):
                # copy to output
                shutil.copy2(self.path, path)
            else:
                # Just use convert directly, then copy
                # metadata with exiftool.
                com = ["convert"]
                com.extend(res_opts)
                com.extend(qual_opts)
                com.append(self.path)
                com.append(path)
                proc_export = sp.Popen(com, stdout=None, stderr=None,
                    stdin=None)
                proc_export.wait()
                proc_meta = sp.Popen(com_meta, stdout=None, stderr=None,
                    stdin=None)
                proc_meta.wait()


class Video(object):

    def __init__(self, path, file_time=False):
        self.type = "video"
        self.path = path
        bname = os.path.basename(self.path)
        mat = re.match("(.*)\.(.*)", bname)
        if mat is None:
            raise RuntimeError(\
                "file {} does not have an extension".format(self.path))
        self.root = mat.group(1)
        self.ext = mat.group(2)

        if self.ext.lower() in video_ext:
            self.meta = file_json(self.path)
        else:
            raise RuntimeError("file {} is not a video".format(self.path))

        metadate = file_date(self.path, self.meta, video_date_meta,
            file_time=file_time)

        self.year = metadate["year"]
        self.month = metadate["month"]
        self.day = metadate["day"]
        self.hour = metadate["hour"]
        self.minute = metadate["minute"]
        self.second = metadate["second"]

        self.md5 = file_md5(self.path)
        rname, ckshort = file_rootname(bname)
        self.name = file_ckname(rname, self.md5)
        self.uid = "{}{}{}:{}{}{}:{}".format(self.year, self.month, self.day,
            self.hour, self.minute, self.second, self.name)
        #print("Video ctor {}".format(self.path))
        #print("  name = {}".format(self.name))
        #print("  root = {}, ext = {}".format(self.root, self.ext))
        #print("  md5 = {}".format(self.md5))
        #print("  {}-{}-{} {}:{}:{}".format(self.year, self.month, self.day,
        #    self.hour, self.minute, self.second))
        #print("  UID = {}".format(self.uid))
        #print("  exif:")
        #for k, v in self.meta.items():
        #    print ("    {} = {}".format(k, v))

    def export(self, path, resolution="FULL"):
        pass



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
    stripped, ckshort = file_rootname(full2)
    print(stripped)
    stripped2, ckshort = file_rootname(stripped)
    print(stripped2)
