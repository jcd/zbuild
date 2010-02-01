from lib.utils import dlog
from lib import db, utils, building
import os, os.path
import sys
import re as rex
import datetime

def re(args):
    
    argc = len(args)

    store = db.initdb()

    bs = lookup_or_create_buildset_by_regex(args[1], store)

    # now create that build
    b = db.build.createFromBuildset(bs)

    if not utils.lockPid(OPTIONS.pid_file):
        dlog("Already building in this dir (Pidfile exists) -> aborting")
        return False

    building.run_build(b, store)
    
    # Clean up for next run
    os.remove(OPTIONS.pid_file)

def lookup_or_create_buildset_by_regex(re, store):

    c = rex.compile(re)

    scripts = store.find(db.script)

    matching_scripts = []
    for script in scripts:
        if c.match(script.name):
            matching_scripts.extend(script.getLeafs())
            
    # Lookup the buildset if it exists
    bsname = unicode(re)
    bs = store.find(db.buildset, db.buildset.name == bsname).any()
    if bs is None:
        # Create a custom buildset
        bs = db.buildset()
        bs.name = bsname
        store.add(bs)
        store.commit()

    # add missing scripts 
    for sc in matching_scripts:
        found = False
        for ex_sc in bs.buildset_scripts:
            if ex_sc.script_id == sc.id:
                found = True
                break
        if not found:
            bs.addScript(sc)

    # and remove non-existing
    for ex_sc in bs.buildset_scripts:
        found = False
        for sc in matching_scripts:
            if ex_sc.script_id == sc.id:
                found = True
                break
        if not found:
            bs.removeScript(ex_sc)

    store.commit()

    return bs
