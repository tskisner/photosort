
from __future__ import (absolute_import, division, print_function,
    unicode_literals)

import os
import sys

import sqlite3
import re


class DB(object):


    def __init__(self, path, mode='w'):
        
        self.path = path
        create = True
        if ( os.path.exists(self.path) ):
            create = False

        self.mode = mode
        if ( mode == 'r' ) and ( create ):
            raise RuntimeError("cannot open a non-existent DB in read-only mode")

        self.conn = None
        try:
            # only python3 supports uri option
            if (mode == 'r'):
                self.connstr = 'file:{}?mode=ro'.format(self.path)
            else:
                self.connstr = 'file:{}?mode=rwc'.format(self.path)
            self.conn = sqlite3.connect(self.connstr, uri=True)
        except:
            self.conn = sqlite3.connect(self.path)

        if create:
            self._init_schema()


    def _init_schema(self):
        cur = self.conn.cursor()
        cur.execute('create table media (uid text unique, name text, md5 text unique, year integer, month integer, day integer, hour integer, minute integer, second integer)')
        self.conn.commit()
        return


    def insert(self, obj):
        cur = self.conn.cursor()
        cur.execute('insert into media values (\"{}\", \"{}\", \"{}\", {}, {}, {}, {}, {}, {})'.format(obj.uid, obj.name, obj.md5, int(obj.year), int(obj.month), int(obj.day), int(obj.hour), int(obj.minute), int(obj.second)))
        self.conn.commit()


    def query(self, uid):
        cur = self.conn.cursor()
        cur.execute('select * from media where uid = \"{}\"'.format(uid))
        row = cur.fetchone()
        if row is None:
            return None
        else:
            return tuple(row)


    def query_md5(self, chksum):
        cur = self.conn.cursor()
        cur.execute('select * from media where md5 = \"{}\"'.format(chksum))
        row = cur.fetchone()
        if row is None:
            return False
        else:
            return True



if __name__ == "__main__":

    from media import Image

    path = sys.argv[1]
    imgpath = sys.argv[2]

    db = DB(path)
    img = Image(imgpath)

    result = db.query(img.uid)
    if result is not None:
        print('result was not None!')

    db.insert(img)
    result = db.query(img.uid)
    if result is None:
        print('result was None!')

    chk = db.query_md5(img.md5)
    if not chk:
        print('cannot find md5 sum {}!'.format(img.md5))

    print(result)


