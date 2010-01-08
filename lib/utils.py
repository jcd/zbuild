#!/usr/bin/python
# -*- coding: utf-8;tab-width: 4; mode: python; indent-tabs-mode: nil -*-
"""
Utilities
"""

import os.path
import os
import sys

DEBUG = True

# Debug logging to console
log_indent = 0
indent = "    "
def dlog(msg, obj = None):
    if DEBUG:
        print (indent * log_indent) + msg
    if obj:
        obj.log += msg + u"\n"


def log_stdout():
    """
    Helper log function to return a function that can be used to log
    to a build db entry
    """
    f = open('./build.log', 'w')
    def do_log(msg):
        sys.stdout.write(msg)
        sys.stdout.flush()
        f.write(msg)
        f.flush()
    return do_log

def mkdirp(path):
    """
    Ensure that path of dirs exists
    """
    ps = path.split('/')
    fpath = ""
    for p in ps:
        fpath += p + "/"
        if not os.path.exists(fpath):
            os.mkdir(fpath)
        elif not os.path.isdir(fpath):
            raise Exception("Cannot chdir '%s' because is it a file" % (fpath,))
    

def lockPid(pid_file):
    """Get an exclusive lock when building"""
    # If a running zbuild is present then abort
    if os.path.exists(pid_file):
        return False

    # Run next scheduled build
    global pid
    pid = os.getpid()

    # Create pid_file to signal that a build is in progress
    runfile = open(pid_file, 'w')
    runfile.write(str(pid))
    runfile.flush()
    runfile.close()
    return True

def sec2str(secs):
    """
    Format seconds to HH:MM:SS or MM:SS if not enough seconds for an
    hour
    """
    secs = int(secs)
    h = secs / (60*60)
    m = (secs - (h*60*60)) / 60
    s = secs - (h*60*60 + m * 60)
    res = str(m).rjust(2,'0') + ":" + str(s).rjust(2,'0')
    if h:
        return str(h).rjust(2,'0') + ":" + res
    return res

def render_tree_entry(cur, last = None, num = None, num_len = 2):
    indent = "   "
    common, path = cur.getPathChange(last)
    idx = len(common)
    res = ""
    
    for path_entry in path:
        
        idx += 1
        
        if path_entry != cur:
            if num is not None:
                res += str(num).rjust(num_len,'0') + " "
                num += 1    
            res += (indent * idx) + path_entry.name + "\n"
            continue
        
        if num is not None:
            res += str(num).rjust(num_len,'0') + " "
        res += (indent * idx)

        break
    return res, num
