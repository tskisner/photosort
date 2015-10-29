
import os
import sys
import shutil
import re
import argparse

import photosort as ps


def find_top_dir():
    cursor = os.path.getcwd()
    while os.path.dirname(cursor) != '/':
        test = os.path.join(cursor, 'albums')
        if os.path.isdir(test):
            return cursor
        cursor = os.path.dirname(cursor)
    raise RuntimeError("work directory is not within an image tree")
    return ""


def main():
    parser = argparse.ArgumentParser( description='Create albums with symbolic links.' )
    parser.add_argument( '--album', required=True, help='album name' )
    args = parser.parse_args()
    topdir = find_top_dir()
    ps.album_append(topdir, args.album, argv)


if __name__ == "__main__":
    main()

