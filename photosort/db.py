
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
        cur.execute('create table img (uid text unique, name text, md5 text unique, year integer, month integer, day integer, hour integer, minute integer, second integer)')
        cur.execute('create table tags (uid text, tagstr text, foreign key(uid) references img(uid))')
        self.conn.commit()
        return


    def insert(self, im):
        cur = self.conn.cursor()
        cur.execute('insert into img values (\"{}\", \"{}\", \"{}\", {}, {}, {}, {}, {}, {})'.format(im.uid, im.name, im.md5, int(im.year), int(im.month), int(im.day), int(im.hour), int(im.minute), int(im.second)))
        tagstr = ','.join(im.tags)
        cur.execute('insert into tags values (\"{}\", \"{}\")'.format(im.uid, tagstr))
        self.conn.commit()


    def query(self, uid):
        cur = self.conn.cursor()
        cur.execute('select * from img where uid = \"{}\"'.format(uid))
        row = cur.fetchone()
        if row is None:
            return None
        else:
            cur.execute('select * from tags where uid = \"{}\"'.format(uid))
            tagrow = cur.fetchone()
            tags = []
            if tagrow is not None:
                tags = list(tuple(tagrow))
            return tuple(row).append(tags)


    def query_md5(self, chksum):
        cur = self.conn.cursor()
        cur.execute('select * from img where md5 = \"{}\"'.format(chksum))
        row = cur.fetchone()
        if row is None:
            return False
        else:
            return True



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

    chk = db.query_md5(img.md5)
    if not chk:
        print('cannot find md5 sum {}!'.format(img.md5))

    print(result)


