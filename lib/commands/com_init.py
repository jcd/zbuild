from lib.utils import dlog, mkdirp
from lib import db
import os, os.path
import sys

def init(args):
    
    argc = len(args)

    if not os.path.isdir(OPTIONS.work_dir):
        print "Creating work dir '%s'" % OPTIONS.work_dir
        mkdirp(OPTIONS.work_dir)

    store = db.initdb(False)
    if store:
        dlog("This is already a zbuild dir")
        return

    db.initdb(True)

    if not os.path.isdir(OPTIONS.build_area):
        # print "Creating build dir '%s'" % OPTIONS.build_area
        mkdirp(OPTIONS.build_area)

    if not os.path.isdir(OPTIONS.released_debs_path):
        # print "Creating release dir '%s'" % OPTIONS.released_debs_path
        mkdirp(OPTIONS.released_debs_path)
