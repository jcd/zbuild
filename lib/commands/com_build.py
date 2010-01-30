from lib.utils import dlog
from datetime import datetime
from lib import utils, db, building
import os
import sys

def build(args):

    argc = len(args)
    
    store = db.initdb()

    if argc < 2:
        dlog("Usage: %s build <buildset name/idx>" % sys.argv[0])
        dlog("\nAvailable buildsets:\n")
        db.buildset.dumpNames(store,  sys.stdout.write)
        return False
                    
    buildset = db.buildset.getByIdent(store, unicode(args[1]))

    if not buildset:
        print u"Error: No buildset called '%s'" % unicode(args[1])
        # Clean up for next run
        os.remove(OPTIONS.pid_file)
        return

    print u'Using buildset "%s"' % buildset.name

    build = db.build.createFromBuildset(buildset)

    if not utils.lockPid(OPTIONS.pid_file):
        dlog("Already building in this dir (Pidfile exists) -> aborting")
        return False

    building.run_build(build, store)
    
    # Clean up for next run
    os.remove(OPTIONS.pid_file)
