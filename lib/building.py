#!/usr/bin/python
# -*- coding: utf-8;tab-width: 4; mode: python; indent-tabs-mode: nil -*-
"""

Methods for executing the builds

"""

from utils import dlog, mkdirp, log_stdout
from datetime import datetime, timedelta
import select
import os.path

use_popen2 = True
try:
    from subprocess import Popen, PIPE
    use_popen2 = False
except:
    import popen2

from storm.locals import *
import db

def run_build(build, store):
    """
    Run any build specified in the database to be build.
    
    This is the main entry.
    """

    # Run scripts in the buildset in the context of the build settings
    dlog("Starting build of buildset " + build.buildset.name)

    # Make sure that the build dir is present
    co_dir = os.path.expanduser(OPTIONS.build_area)
    mkdirp(co_dir)

    build.work_dir = unicode(co_dir)
    build.start_time = datetime.utcnow()

    store = Store.of(build)
    store.commit()
 
    # Run all scripts in this buildset
    index = 0

    # Run script
    logger = log_stdout()

    bs = store.find(db.build_script_status,  
                    db.build_script_status.build_id == build.id).order_by(Asc(db.build_script_status.idx)) 
    build_script_statuses = map(lambda a: a, bs)
    store.commit()

    for build_status in build_script_statuses:

        build_status.start_time = datetime.utcnow()
        store.commit()

        dlog("------------------------------------------------------------------")

        if OPTIONS.stop_index <= index:
            dlog("Skipping rest of scripts in buildset as requested by set option", build_status)
            break

        if OPTIONS.start_index > index:
            dlog("Skipping by until index " + str(OPTIONS.start_index) + " (current step " + str(index) + ")",
                 build_status)
            index += 1
            continue

        index += 1
        def do_log(msg):
            logger(msg)
            build_status.log += unicode(msg)
        ss = build_status.buildset_script

        if ss.script:
            scriptpath = build_status.buildset_script.script.path
            build_status.exit_code = run_script(do_log, scriptpath)
            #    run_script(do_log, spath + os.sep + build_status.buildset_script.script.path)

        build_status.end_time = datetime.utcnow()
        if not build_status.exit_code:
            build_status.buildset_script.last_duration = (build_status.end_time - 
                                                          build_status.start_time).seconds

    build.end_time = datetime.utcnow()
    store.commit()

    #buildset.updateMetadata(timings=timings)

    #timings[None] = (buildset.name, end_time - start_time)
    
    dlog("Build completed")


def run_script(logger, path):
    """
    Run the script specified on path sending log status to logger.
    """
    SCRIPT_TIMEOUT=30*60  # seconds before the script times out
    CHECK_INTERVALS=1.0    # second between each status check of script
    
    dlog("Running script " + path)
    begin_time = datetime.utcnow()
    
    # When to kill the script because it has been running for too long
    kill_time = begin_time + timedelta(seconds=SCRIPT_TIMEOUT)

    init_bash = OPTIONS.zbuild_install_dir + "/lib/functions.sh"

    # As a convenience set the pythonpath to include the workdir
    pp = os.environ.get('PYTHONPATH', None)
    os.environ['PYTHONPATH'] = OPTIONS.pwd + ( pp and (":" + pp) or '') 

    if use_popen2:
        inst = popen2.Popen3("/bin/bash %s '%s'" % (init_bash, path), True)
        out, _in, err = inst.fromchild, inst.tochild, inst.childerr
    else:
        inst = Popen(["/bin/bash", init_bash, path],  
                  stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True)
        # TODO: use communicate instead
        out, _in, err = inst.stdout, inst.stdin, inst.stderr
        
    # Iterate until script is done or should be killed
    dot_last = True

    global first_line
    first_line = True

    def do_logging(dot_last):
        """
        Read output from pipe and put to our logger
        """
        rlist, wlist, xlist = select.select([out,err], [], [], CHECK_INTERVALS)

        global first_line

        # append output to log buffers
        if len(rlist):
            #if dot_last:
            #    logger("\n")
            msg = None
            pre = ' '
            if out in rlist:
                msg = os.read(out.fileno(), 1000)
            if err in rlist:
                msg = os.read(err.fileno(), 1000)
                pre = 'e'
            if msg is not None:
                msgs = msg.split('\n')
                msgs.reverse()
                if len(msgs) == 1:
                    msg = msg
                else:
                    msg = reduce(lambda a, b: b +  ("\n%s %s" % (pre,a)), msgs)
                    #msg = reduce(lambda a, b: b + (a != '' and ("\n%s %s" % (pre,a)) or ''), msgs)
                if msg is not None:
                    logger((first_line and ("%s " % pre) or '') + msg)

            dot_last = False
            first_line = False
            
        if not (len(xlist) or len(rlist) or len(wlist)) and dot_last:
            logger(".")
            dot_last = True

        return dot_last

    while datetime.utcnow() < kill_time and inst.poll() < 0:
        dot_last = do_logging(dot_last)

    # Last chance logging in case of instant termination of proc
    do_logging(dot_last)
    
    res = inst.poll()
    
    if res < 0:
        # timed out. kill process.
        del inst
        dlog("Script timed out " + path)
    elif res > 0:
        dlog("Script exited with code " + str(res))

    return res
