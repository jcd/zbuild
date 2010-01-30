from lib.utils import dlog
from lib import utils, db
from storm.locals import *

def status(args):

    argc = len(args)

    store = db.initdb()

    pid = None
    try:
        pid = open(OPTIONS.pid_file, 'r').read()
    except:
        pass

    show_count = 1
    build_id = None
    if argc > 1:
        if args[1] == 'last':
            try:
                show_count = int(args[2])
            except:
                pass
        else:
            try:
                build_id = int(args[1])
            except:
                pass
        
    if build_id:
        builds = store.find(db.build, db.build.id == build_id).order_by(Desc(db.build.id))
    else:
        builds = store.find(db.build).order_by(Desc(db.build.id))

    if not builds.count():
        dlog("No builds available")

    build_num = 1

    for build in builds:
        dlog("Buildset '%s' (build %i)" % (build.buildset.name, build.id))
        dlog("-" * 50)
        indent = "   "
        last_script = None

        bs = store.find( db.build_script_status,
                         db.build_script_status.build_id == build.id,
                         db.buildset_script.id == db.build_script_status.buildset_script_id).order_by(Asc(db.buildset_script.idx))

        for status in bs:
            fmt = "%-18s : %-9s (%s of %s)"
            script = status.buildset_script.script
            start_time = status.start_time
            end_time = status.end_time or datetime.utcnow()
            dur = (not start_time) and "--:--" or utils.sec2str((end_time - start_time).seconds)
            eta_dur = status.buildset_script.last_duration
            eta_dur = eta_dur is not None and utils.sec2str(eta_dur) or "--:--"

            # print parent scripts that was not parent for the
            # last script
            lines, num = utils.render_tree_entry(script, last_script)
            last_script = script

            if status.end_time:
                status_str = (not status.exit_code and "Success" or "Failure")
                #              ("exit(" + str(status.exit_code) + ")") )
            else:
                status_str = status.start_time and "Running" or "  -"

            while len(lines) != 1:
                dlog(lines.pop(0))
                
            dlog(fmt % ( lines[-1] + script.name, status_str, dur, eta_dur ))

        dur, eta_dur = build.getDurations()
        dlog("-" * 50)
        dlog("%-33s (%s of %s) " % ("Total duration", 
                              utils.sec2str(dur or 0), 
                              utils.sec2str(eta_dur or 0) 
                              ))
        dlog("")
        if show_count == build_num:
            break
        build_num += 1
    return

    f = open(os.path.expanduser(OPTIONS.work_dir) + "/" + pid, 'r')
    timings = pickle.load(f)

    buildset = buildsets.buildsets[timings[None][1]]
    now = datetime.utcnow()
    dur = now - timings[None][0]
    print "Buildset '" + buildset.name + "' progress " + str(dur).split('.')[0] + " of " + str(buildset.metadata.get('duration','n/a')).split('.')[0]
    del timings[None]

    keys = timings.keys()
    keys.sort()

    for pack in keys:
        symlink = os.readlink("buildsets/" + buildset.name + "/" + pack)
        script = buildsets.get_script_by_buildset_link(symlink)
        dur = script.metadata.get('duration','n/a')
        cur_dur = timings[pack]

        if type(cur_dur) is datetime:
            print "  Script '" + script.name + "' " + str(now - cur_dur).split('.')[0] + " of " + str(dur).split('.')[0]
        else:
            print "  Script '" + script.name + "' " + str(cur_dur).split('.')[0] + " done"
