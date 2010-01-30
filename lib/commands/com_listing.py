from lib.utils import dlog
from lib import db
import os, os.path
import sys

def listing(args):
    
    argc = len(args)

    store = db.initdb()

    sub = ""
    if argc > 1:
        sub = args[1]

    if sub in ('scripts','buildsets',''):
        _listing_list(store, sub)
    else:
        buildset_ident = unicode(args[1])
        _listing_buildset(store, buildset_ident)
                    
  
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
