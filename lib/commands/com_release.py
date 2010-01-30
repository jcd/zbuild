
def release(args):

    store = db.initdb()

    try:
        pid = open(OPTIONS.pid_file, 'r').read()
    except:
        # ok
        pass
    else:
        print "Cannot release this buildset since it is still building. Please hang on."
        sys.exit(1)

    # Make tags in the git/svn repos named from the release version. Possibly
    # moving a tag. (or commit version info to repos?)
    
    
    # Upload "binaries" to public repos
    p = OPTIONS.released_debs_path
