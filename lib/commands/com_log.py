from lib.utils import dlog
from lib import db

def log(args):

    argc = len(args)

    pid = None
    try:
        pid = open(OPTIONS.pid_file, 'r').read()
    except:
        pass

    store = db.initdb(False)
    if not store:
        if pid:
            dlog("Error: database empty!")
        else:
            dlog("No build results available")
        return
    
    builds = store.find(db.build).order_by(Desc(db.build.id))
    if not builds.count():
        dlog("No builds available")
        
    for build in builds:
        dlog("Buildset '%s'" % build.buildset.name)
        indent = "   "
        last_script = None

        bs = store.find( db.build_script_status,
                         db.build_script_status.build_id == build.id,
                         db.buildset_script.id == db.build_script_status.buildset_script_id).order_by(Asc(db.buildset_script.idx))

        idx = 0
        for status in bs:
            if idx < options.start_index and idx > options.stop_index:
                idx += 1
                continue
            script = status.buildset_script.script
            dlog("-" * 70)
            dlog("Log for '%s'" % script.name)
            dlog(status.log)
            dlog("-" * 70)
            idx += 1
            
        break
