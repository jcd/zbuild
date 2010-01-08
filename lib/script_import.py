#!/usr/bin/python
# -*- coding: utf-8;tab-width: 4; mode: python; indent-tabs-mode: nil -*-
"""

  Functions for importing scripts into database

"""

import commands
import os.path

from storm.locals import *
import db

def import_scripts(path, store):
    """
    Import scripts in path into database
    """

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

    base_path_len = len(pathlist[0])
    if path[-1] != '/':
        base_path_len += 1

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
            print "Skipping %s because it is already present in build system" % str(tuple(script_path))
            continue

        p = db.script()
        p.name = unicode(script_name)
        p.path = unicode(full_path) # absolute path
        p.parent_id = scripts.get( tuple(script_path[:-1]) )
        is_parent = os.path.isdir(full_path)
        p.is_parent = is_parent and 1 or 0
        print full_path
        store.add(p)
        store.flush()

        if is_parent:
            # print "is parent %i" % p.id
            scripts[tuple(script_path)] = p.id
            
        print "Adding %s : % s" % (p.id, fname)

    store.commit()
