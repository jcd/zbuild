from lib.utils import dlog
from lib import db, utils, building
import os, os.path
import sys
import re as rex
import datetime

def re(args):
    
    argc = len(args)

    store = db.initdb()

    c = rex.compile(args[1])

    scripts = store.find(db.script)

    matching_scripts = []
    for script in scripts:
        if c.match(script.name):
            matching_scripts.extend(script.getLeafs())
            
    # Lookup the buildset if it exists
    bsname = unicode(args[1])
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

    # now create that build
    b = db.build.createFromBuildset(bs)

    if not utils.lockPid(OPTIONS.pid_file):
        dlog("Already building in this dir (Pidfile exists) -> aborting")
        return False

    building.run_build(b, store)
    
    # Clean up for next run
    os.remove(OPTIONS.pid_file)

def _listing_list(store, sub):

    if sub == "":
        print "sub commands for this command :"
        print "  buildsets  : to list available buildsets only"
        print "  scripts    : to list available scripts only"
        print "  <name/idx> : the name or index of a buildset to list "
        print "               scripts in that buildset"

    if sub == "scripts":

        # print "\nAvailable scripts:\n"
        db.script.dumpNames(store,  sys.stdout.write)

    if sub in ("buildsets", ''):
        if sub == "":
            print "\nAvailable buildsets:\n"

        db.buildset.dumpNames(store,  sys.stdout.write)

def _listing_buildset(store, buildset_ident):

    # A specific buildset has been specified. List that.
    buildset = db.buildset.getByIdent(store, buildset_ident)

    if not buildset:
        dlog("Error: No such buildset " + buildset_ident)
        return False
        
    print "\nScripts executed in buildset '" + buildset.name + "':\n"

    db.buildset.dumpScriptNames(buildset,  sys.stdout.write)

    print ""
