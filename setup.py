#!/usr/bin/env python

import os
import sys
import re

from setuptools import find_packages, setup, Extension


def get_version():
    ver = 'unknown'
    if os.path.isfile("photosort/_version.py"):
        f = open("photosort/_version.py", "r")
        for line in f.readlines():
            mo = re.match("__version__ = '(.*)'", line)
            if mo:
                ver = mo.group(1)
        f.close()
    return ver

current_version = get_version()


setup (
    name = 'photosort',
    provides = 'photosort',
    version = current_version,
    description = 'Sort photos based on EXIF data',
    author = 'Theodore Kisner',
    author_email = 'mail@theodorekisner.com',
    url = 'https://github.com/tskisner/photosort',
    packages = [ 'photosort' ],
    scripts = [ 'phts_sync', 'phts_dirmd5', 'phts_album', 'phts_verify', 'phts_fixdate',
                'phts_info', 'phts_export', 'phts_convert_video' ],
    license = 'None',
    requires = ['Python (>3.3.0)', ]
)

