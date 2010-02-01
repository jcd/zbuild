#!/usr/bin/python
# -*- coding: utf-8;tab-width: 4; mode: python; indent-tabs-mode: nil -*-
"""

  Functions for importing scripts into database

"""

import sys
import commands
import os.path, os

from storm.locals import *
from lib import db

def sync(args):
    argc = len(args)
    
    store = db.initdb()

    path = argc > 1 and args[1]
    if path == False:
        print "Needs path of scripts to sync recusively."
        sys.exit(1)

    sync_scripts(path, store)

def download_scripts_from_git(url, path, repos_name, to_path):
    """
    Download the path in the repository specified by url to to_path

    This implementation is NOT safe and should be reimplemented
    """
    print "Downloading remote zbuild scripts : %s in dir %s" % (url, path)

    # git archive --prefix=hest/ --remote="jcd@localhost:Projects/zbuild" HEAD test/scripts > test.tar

    tar_path = to_path + os.path.sep + repos_name + ".tar"
    (status, output) = commands.getstatusoutput("git archive --remote='%s' --prefix='%s/' HEAD '%s' > '%s'" %
                                             (url, repos_name, path, tar_path))
    if status:
        print output
        return False
    else:
        print "Done downloading"

    path_start = path.split(os.path.sep)[0]
    (status, output) = commands.getstatusoutput("cd '%s' && tar -xf '%s' && mv %s/* %s/ && rm -rf %s %% rm %s" %
                                                (to_path, repos_name + ".tar",
                                                 repos_name + os.path.sep + path, repos_name,
                                                 repos_name + os.path.sep + path_start, repos_name + ".tar"))
    if status:
        print output
        return False
    else:
        print "Done extracting"

    return True


def sync_scripts(path, store):
    """
    Import scripts in path into database. Path can be:
    1, a path on the filesystem e.g. ./myscripts
    2, a git repository e.g. https://hosting.com/myrepos.git#path/to/scripts
    """

    fragment_idx = path.find('#')
    repos = None

    if fragment_idx > 0:
        # This is a git url
        repos = path
        url = path[:fragment_idx]
        gitpath = path[fragment_idx+1:]
        repos_url_toks = url.split('/')
        repos_name = repos_url_toks[-1] or repos_url_toks[-2]

        # get scripts from repository
        path = (OPTIONS.work_dir + os.path.sep +
                   'repos_scripts')
        if not os.path.exists(path):
            os.mkdir(path)
        
        if not download_scripts_from_git(url, gitpath, repos_name, path):
            print "Error syncronizing scripts from remote repository"
            return False
        
    path = os.path.abspath(os.path.expanduser(path))

    scripts = {}
    def get_parent(ps,  name):
        for i in ps:
            if name[:len(i)] == i:
                return ps[i]
        return None

    if not os.path.isdir(os.path.expanduser(path)):
        print "Error: Cannot import scripts from non-existing dir '%s'" % path
        return
        
    pathlist = commands.getoutput("find %s | sort" % (path,))
    pathlist = pathlist.split('\n')
    idx = 0

    def is_exec(pp):
        st = os.stat(pp)
        return ( ( (st.st_mode & os.path.stat.S_IXUSR) and st.st_uid == os.getuid()) or
                 ( (st.st_mode & os.path.stat.S_IXGRP) and st.st_uid in os.getgroups()) or
                 ( st.st_mode & os.path.stat.S_IXOTH and st.st_uid != os.getuid() ) )

    base_path_len = len(pathlist[0])
    if path[-1] != '/':
        base_path_len += 1

    existing_ids = set()
    
    for full_path in pathlist:

        fname = full_path[base_path_len:]

        if not fname:
            # This is the import dir itself
            continue

        script_path = fname.split('/')
        script_name = script_path[-1]

        #dlog("script_path %s path is %s" % (str(script_path),str(script_path)))

        if script_name[0] in ['.', '#'] or script_name[-1] == '~':
            # skip unwanted files
            continue

        # Create or lookup script group if any by using the the dirs
        # up to the script_name 
        # Skip script if it already exists
        p = store.find(db.script, db.script.path == unicode(full_path)).one()

        if p:
            scripts[tuple(script_path)] = p.id
            print "Existing %s" % str('/'.join(script_path)),
            if False and not is_exec(full_path):
                print " -> removing because not executable anymore"
                for bss in p.buildset_scripts:
                    store.remote(bss)
                store.remove(p)
                store.commit()
            else:
                existing_ids.add(p.id)
            continue

        if not is_exec(full_path):
            continue

        p = db.script()
        p.name = unicode(script_name)
        p.repos = unicode(repos)
        p.path = unicode(full_path) # absolute path
        p.parent_id = scripts.get( tuple(script_path[:-1]) )
        is_parent = os.path.isdir(full_path)
        p.is_parent = is_parent and 1 or 0
        # print full_path
        store.add(p)
        store.flush()

        existing_ids.add(p.id)

        if is_parent:
            # print "is parent %i" % p.id
            scripts[tuple(script_path)] = p.id
            
        print "Adding %s : % s" % (str(p.id).rjust(2), fname)

    # Remove scripts not present anymore
    # TODO: hmmmm
    
    store.commit()
