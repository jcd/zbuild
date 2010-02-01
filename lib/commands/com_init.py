from lib.utils import dlog, mkdirp
from lib import db
import os, os.path
import sys
import shutil
import commands
import com_sync
import com_re

def init(args):
    
    argc = len(args)        
        
    # If there is an argument present it is a repository to checkout
    # and cd into
    if argc > 1:
        repos = args[1]
        (status, output) = commands.getstatusoutput("git clone '%s' " % repos)
        if status:
            # Error checking out the repository
            print output
            print status
            return False

        # Now re-run the zbuild init command with any args
        repos_toks = repos.split('/')
        repos_name = repos_toks[-1] or repos_toks[-2]
        os.chdir(repos_name.endswith(".git") and repos_name[-4:] or repos_name)

        (status, output) = commands.getstatusoutput("%s/zbuild init" % OPTIONS.zbuild_install_dir)
        print output
        if status:
            # Error checking out the repository
            print status
            return False
        return True

            
    if not os.path.isdir(OPTIONS.work_dir):
        print "Creating zbuild working dir '%s'" % OPTIONS.work_dir
        mkdirp(OPTIONS.work_dir)

    if not os.path.isdir(OPTIONS.build_area):
        # print "Creating build dir '%s'" % OPTIONS.build_area
        mkdirp(OPTIONS.build_area)

    if not os.path.isdir(OPTIONS.released_debs_path):
        # print "Creating release dir '%s'" % OPTIONS.released_debs_path
        mkdirp(OPTIONS.released_debs_path)

    store = db.initdb(False)
    if store:
        dlog("This is already a zbuild dir")
        return

    store = db.initdb(True)

    script_dir = OPTIONS.work_dir + os.path.sep + "scripts"

    created_default_scripts = False
    
    if not os.path.isdir(OPTIONS.work_dir + os.path.sep + "scripts"):
        # Create a default scripts setup for this project to make it
        # easy to get started.
        shutil.copytree(OPTIONS.zbuild_install_dir + os.path.sep +
                        "lib" + os.path.sep + "script_templates",
                        script_dir)

        
        created_default_scripts = True

        print "Installed a script dir for your convenience in %s " % script_dir
        print "You may modify files in there to fit your needs or add new ones."

        # If we have a Rakefile in curdir we may have the posibility
        # to run rake tests. Offer to use rake tests in as default.
        # TODO...

    # Make all scripts visible by syncing
    com_sync.sync_scripts(script_dir, store)

    if created_default_scripts:
        # Create buildsets for builtin regex builds
        for builtin_re in ['unittest', 'functest', 'stage', 'release']:
            com_re.lookup_or_create_buildset_by_regex(builtin_re, store)

    print "Use 'zbuild list' for a listing of currently available buildsets"
