from lib.utils import dlog
from datetime import datetime
from lib import utils, db, building
import os
import sys

def enqueue(args):

    argc = len(args)
    
    store = db.initdb()

    if argc < 2:
        dlog("Usage: %s enqueue <buildset name/idx>" % sys.argv[0])
        dlog("\nAvailable buildsets:\n")
        db.buildset.dumpNames(store,  sys.stdout.write)
        return False
                
    if not utils.lockPid(OPTIONS.pid_file):
        dlog("Pidfile already exists -> aborting")
        return False
    
    buildset = db.buildset.getByIdent(store, unicode(args[1]))

    if not buildset:
        print u"Error: No buildset called '%s'" % unicode(args[1])
        # Clean up for next run
        os.remove(PID_FILE)
        return

    print u'Using buildset "%s"' % buildset.name

    build = db.build.createFromBuildset(buildset)

    building.run_build(build, store)
    
    # Clean up for next run
    os.remove(OPTIONS.pid_file)

