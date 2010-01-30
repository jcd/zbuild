
def buildinfo(args):

    versions_file = "versions"

    if argc > 1:
        pack = args[1]
    else:
        print "Need script name as argument"
        sys.exit(1)
        
    if argc > 2:
        versions_file = args[2]


    if not os.path.isfile(versions_file):
        print "Cannot open provided versions file '%'" % (versions_file)
        sys.exit(1)

    # Get the info from versions file
    import ConfigParser
    config = ConfigParser.SafeConfigParser()
    config.read(versions_file)

    if not config.has_section('scm'):
        print "Need section [scm] in versions config file"
        sys.exit(1)
        
    scm = {}
    for opt in config.OPTIONS('scm'):
        scm[opt] = config.get('scm', opt)

    if not config.has_section('scripts'):
        print "No [scripts] section in versions config file"
        sys.exit(1)

    if not config.has_option('scripts', pack):
        print "No script named '%s' in versions config file" % (pack,)
        sys.exit(1)

    info = { 'repos' : '', 'repos_uri' : '', 'script' : pack, 'revision': 'HEAD', 'branch': ''}
    pi = config.get('scripts',pack)
    pi = pi.split(' ')

    if config.has_option('scm', pi[0]):
        info['repos'] = pi[0]
        info['repos_uri'] = scm[pi[0]]
    pi = pi[1].split(':')

    info['branch'] = pi[0]
    if len(pi) > 1:
        info['revision'] = pi[1]

    for i in info:
        print i + " " + info[i]
