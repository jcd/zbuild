    store = db.initdb()

        # Schedule a build for later
        if not initdb(False):
            dlog("Error: database empty - use 'zbuild sync' to populate")
            return

        if argc < 3:
            dlog("Usage: %s schedule <buildset name/idx> < '[yyyy-mm-dd] hh:mm' >" % sys.argv[0])
            dlog("\nAvailable buildsets:\n")
            db.buildset.dumpNames(STORE,  sys.stdout.write)
            return False

        scheduled_for = datetime.utcnow()
        try:
            # 'yyyy-mm-dd hh:mm' format
            scheduled_for = datetime.strptime(args[2], '%Y-%m-%d %H:%M')
        except:
            # 'hh:mm' format
            try:
                scheduled_for = datetime.strptime(args[2], '%H:%M')
            except:
                dlog("Error: The schedule time has wrong format '%s'" % args[2])
                dlog("Usage: %s schedule <buildset name/idx> < '[yyyy-mm-dd] hh:mm' >" % sys.argv[0])
                return False
            
        buildset = db.buildset.getByIdent(STORE, unicode(args[1]))
        if not buildset:
            print u"Error: No buildset called '%s'" % unicode(args[1])
            return

        print u'Using buildset "%s"' % buildset.name

        build = db.build.createFromBuildset(buildset)
        build.scheduled_for = scheduled_for
        STORE.commit()
        
