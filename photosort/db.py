
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

        if (mode == 'r'):
            self.connstr = 'file:{}?mode=ro'.format(self.path)
        else:
            self.connstr = 'file:{}?mode=rwc'.format(self.path)
        self.conn = sqlite3.connect(self.connstr, uri=True)

        if create:
            self._init_schema()


    def _init_schema(self):
        cur = self.conn.cursor()
        cur.execute('create table img (uid text unique, name text, md5 text, year integer, month integer, day integer)')
        self.conn.commit()
        return


    def insert(self, im):
        cur = self.conn.cursor()
        cur.execute('insert into img values (\"{}\", \"{}\", \"{}\", {}, {}, {})'.format(im.uid, im.name, im.md5, int(im.year), int(im.month), int(im.day)))
        self.conn.commit()


    def query(self, uid):
        cur = self.conn.cursor()
        cur.execute('select * from img where uid = \"{}\"'.format(uid))
        row = cur.fetchone()
        if row is None:
            return None
        else:
            return tuple(row)



if __name__ == "__main__":

    from image import Image

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

    print(result)


