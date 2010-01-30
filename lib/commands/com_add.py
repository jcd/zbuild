import sys
from lib import db
from lib.utils import dlog

def remove(args):
    return add(args)

def add(args):

    argc = len(args)
    
    # Add specified script to buildset
    
    # allow creating the database if this is a addscript
    store = db.initdb()

    command = args[0]

    if argc < 3:
        if command == "add":
            dlog("Usage: %s add <buildset name/idx> <script name/idx> [before name/idx]" % sys.argv[0])
            dlog("       if before idx is not provided, the script will be")
            dlog("       inserted at end of buildset")
        else:
            dlog("Usage: %s rm <buildset name/idx> <script name/idx>" % sys.argv[0])
        return False

    buildset_ident = unicode(args[1])
    buildset = db.buildset.getByIdent(store, buildset_ident)
    idents = map(lambda a: a.strip(), unicode(args[2]).split(','))

    for ident in idents:
        pack_ident = unicode(ident)
    
        pack = db.script.getByIdent(store, pack_ident)
        
        if buildset is None and command == 'rm':
            dlog("Error: No such buildset " + buildset_ident)
            return False
        
        if pack is None:
            dlog("Error: No such script " + pack_ident)
            return False
        
        if buildset is None:
            dlog("No such buildset " + args[1] + " -> Adding")
            buildset = db.buildset()
            buildset.name = buildset_ident
            store.add(buildset)
            store.flush()
            
        if command == "add":
            pack_idx = sys.maxint
            if argc > 3:
                before_pack = db.script.getByName(store,  unicode(args[3])) # before name
                if before_pack:
                    pack_idx = buildset.getScriptIndex(before_pack)
                else:
                    pack_idx = int(args[3])

            scripts = pack.getLeafs()
            for i in scripts:
                dlog("Adding script %s to buildset %s" % (i.name, buildset.name))
                buildset.addScript(i,  pack_idx)
        else:
            try:
                idx = int(pack_ident)
            except:
                idx = pack
            buildset.removeScript(idx)
    store.commit()
    return True
        
