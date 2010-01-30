from storm.locals import *
from layout import table_layout,  counter_length
import sys
from datetime import datetime, timedelta
import utils
import os.path
import sqlite3

def initdb(allow_create = False):
    """
    Open database STORE - creating it if necessary
    """
    sqlitepath = "%s/zbuild.sqlite" % OPTIONS.work_dir
    if not os.path.exists(sqlitepath):
        if not allow_create:
            return None

        # setup the sqlite database
        # print "No existing sqlite database -> creating"
        schema = "lib/dbschema.sql"
        if not os.path.exists(schema):
            schema = OPTIONS.zbuild_install_dir + "/lib/dbschema.sql"
            if not os.path.exists(schema):
                schema = "/usr/share/zbuild/lib/dbschema.sql"

        # print "Using %s" % sqlitepath 
        conn = sqlite3.connect(sqlitepath)
        conn.executescript(open(schema, 'r').read())
        conn.commit()
        conn.close()
        #os.system("sqlite3 < '%s'" % schema)

    sdb = create_database("sqlite:%s" % sqlitepath)
    return Store(sdb)


class buildset(Storm):
    __storm_table__ = 'buildset'
    id = Int(primary=True)
    name = Unicode()
    flags = Int()
    
    @classmethod
    def dumpNames(cls, store,  os):
        """
        Write all scripts to outstream os
        """
        buildsets = store.find(cls).order_by(cls.id)
        counter_len = counter_length(buildsets.count())
        arr = [ ['idx ', 'name', ' duration'] ]
        idx = 0
        if not buildsets.count():
            os("    No buildsets - use 'addscript' command to add script to a new buildset\n")
            return
        for buildset in buildsets:
            dur = None # buildsets[i].metadata.get('duration',None)
            if dur:
                dur = ':'.join(str(dur).split(':')[1:])
            else:
                dur = "  -"
            arr2 = []
            arr2.append(str(idx).rjust(counter_len,'0'))
            arr2.append(buildset.name)
            arr2.append(" %s" % (str(dur).split('.')[0],))
            arr.append(arr2)
            idx += 1
        os(table_layout(arr, True, "    "))
                
            
    def dumpScriptNames(self, os):
            """
            write list of scripts to logger
            """
            store = Store.of(self)
            pks = store.find(buildset_script, buildset_script.buildset_id == self.id)
            scripts = pks.order_by(Asc(buildset_script.idx))
            counter_len = counter_length(scripts.count())
            arr = [ ['idx ', 'name', ' duration'] ]
            idx = 0

            def scriptPath(_pack):
                """
                """
                res = []
                cur = _pack.script
                while cur.parent:
                    res.insert(0, cur.parent)
                    cur = cur.parent
                return res

            def new(depth, pack_name, pack_idx, dur = None):
                if dur is None:
                    dur = "  -"
                arr2 = []
                arr2.append(pack_idx)
                arr2.append(" " * (depth * 3) + pack_name)
                arr2.append(" %s" % (str(dur).split('.')[0],))
                return arr2

            last_path = []
            for pack in scripts:

                path = scriptPath(pack)
                depth = len(path)
                if last_path != path and depth:
                    arr.append(new(depth - 1,
                                   path[-1].name,
                                   ' '.rjust(counter_len,' ')))
                last_path = path

                dur = None
                # Lookup last duration of script run
                prevrun = store.find(build_script_status, 
                                     build_script_status.buildset_script_id == pack.id,
                                     build_script_status.exit_code == 0
                                     ).order_by(Desc(build_script_status.id)).first()
                
                dur = "  -"
                if prevrun and prevrun.end_time and prevrun.start_time:
                    dur = prevrun.end_time - prevrun.start_time
                    dur = utils.sec2str(dur.seconds)
                arr.append(new(depth,
                               pack.script.name, 
                               str(pack.idx).rjust(counter_len,'0'),
                               dur))
                idx += 1
            os(table_layout(arr, True, "    ", False))
    
    @classmethod
    def getByIndex(cls, store,  idx):
        """
        Get buildset by index
        """
        buildsets = store.find(cls).order_by(cls.id)
        curidx = 0
        for i in buildsets:
            if curidx == idx:
                return i
            curidx += 1
        return None
    
    @classmethod
    def getByName(cls, store, name):
        return store.find(cls,  name == cls.name).one()
    
    @classmethod
    def getByIdent(cls, store, ident):
        try:
            s = cls.getByIndex(store, int(ident))
            if s:
                return s
        except:
            pass
        return cls.getByName(store, ident)
        
    def getScriptIndex(self,  pack):
        """Return the index the given script has in this buildset or None"""
        if type(pack) != script:
            return None
        for i in self.buildset_scripts:
            if i.script_id == pack.id:
                return i.idx
        return None
        
    def addScript(self, pack,  before_script_idx = sys.maxint):
        """Add a new script to this buildset"""
        idx = int(before_script_idx)
        store = Store.of(self)
        pks = store.find(buildset_script, buildset_script.buildset_id == self.id)
        m = pks.max(buildset_script.idx) 
        if m is None:
            # First script is added
            idx = 0
        elif m < idx:
            # append using m+1
            idx = m + 1
        
        # move all tasks with higher or equal index that idx one step
        opks = pks.order_by(Desc(buildset_script.idx))
        for i in opks:
            if i.idx >= idx:
                i.idx += 1
        
        # Create new pack
        spack = buildset_script()
        spack.buildset_id = self.id
        spack.script_id = pack.id
        spack.idx = idx
            
        store.add(spack)
        store.commit()

    def removeScript(self,  pack):
        """Remove script from buildset. Pack is eigther a db.script or an index"""
        idx = self.getScriptIndex(pack)
        if not idx:
            # pack is not a script instance in this buildset, then it must be an index
            idx = int(pack)
            
        store = Store.of(self)
        pks = store.find(buildset_script, buildset_script.buildset_id == self.id)
        opks = pks.order_by(Asc(buildset_script.idx))
        # Correct idx for scripts larger that the one removed
        for i in opks:
            if i.idx == idx:
                store.remove(i)
            elif i.idx > idx:
                i.idx -= 1
        store.commit()

class script(Storm):
    __storm_table__ = 'script'
    id = Int(primary=True)
    name = Unicode()
    repos = Unicode()
    path = Unicode()
    parent_id = Int()
    is_parent = Int()

    def getPath(self):
        """
        Return path of script by constructing an array with parents
        prepended and self as the last entry.
        """
        return self.parent and [self.parent, self] or [self]
    
    def getCanonicalName(self):
        return self.parent and (self.parent.getCanonicalName() + "/" + self.name) or self.name

        return '/'.join(self.getPath())
    
    def getCommonPath(self, other_script):
        """
        Return the part the path (see getPath) that self and
        other_script have in common
        """
        if not other_script:
            return []

        me = self.getPath()

        if self == other_script:
            return me

        other = other_script.getPath()
        res = []

        while me and other and me[0] == other[0]:
            me.pop(0)
            other.pop(0)
            res.append(i1)
        return res        

    def getPathChange(self, other_script):
        """
        Return the part of the path (see getPath) that self and
        other_script does not have in common
        """
        me = self.getPath()

        if self == other_script:
            return (me, [])

        if not other_script:
            return ([],me)

        other = other_script.getPath()
        
        common = []
        while me and other and me[0] == other[0]:
            common.append(me[0])
            me.pop(0)
            other.pop(0)

        return (common, me)

    def depth(self):
        d = 0
        cur = self
        while cur.parent_id:
            d += 1
            cur = cur.parent
        return d


    def getLeafs(self):
        store = Store.of(self)
        scripts = store.find(script, script.parent_id == self.id).order_by(Asc(script.name))

        if scripts.count() == 0:
            return [self]

        res = []
        for i in scripts:
            res.extend(i.getLeafs())
        return res


    @classmethod
    def getIndexedListing(cls, store):
        """
        Return a list of all scripts sorted by script grouping
        """
        scripts = store.find(cls, cls.is_parent == 0).order_by(Asc(cls.parent_id))
        counter_len = counter_length(scripts.count())

        res = []
        last = None
        for s in scripts:
            common, diff = s.getPathChange(last)
            last = s
            res.extend(diff)
        return res


    @classmethod
    def dumpNames(cls, store,  os):
        """
        Write all scripts to outstream os
        """
        idx = 0
        scripts = cls.getIndexedListing(store)
        counter_len = counter_length(len(scripts))
        arr = [ ['idx ','name',' duration'] ]
        
        if not scripts:
            os("    No scripts - use the import-scripts command\n")
            return

        for pack in scripts:
            dur = None # pack.metadata.get('duration',None)
            if dur:
                dur = ':'.join(str(dur).split(':')[1:])
            else:
                dur = "  -"
            arr2 = []
            arr2.append(str(idx).rjust(counter_len,'0'))
            arr2.append(" " * (pack.depth() * 3) + pack.name)
            arr2.append(" %s" % (str(dur).split('.')[0],))
            #arr2.append("%i" % pack.depth())
            arr.append(arr2)
            idx += 1
        os(table_layout(arr, True, "    "))

    @classmethod
    def getByIndex(cls, store,  idx):
        """
        Get buildset by index
        """
        scripts = cls.getIndexedListing(store)
        curidx = 0
        for i in scripts:
            if curidx == idx:
                return i
            curidx += 1
        return None
    
    @classmethod
    def getByName(cls, store, name):
        return store.find(cls, name == cls.name).one()
    
    @classmethod
    def getByIdent(cls, store, ident):
        try:
            s = cls.getByIndex(store, int(ident))
            if s:
                return s
        except:
            pass
        return cls.getByName(store, ident)
        

class buildset_script(Storm):
    __storm_table__ = 'buildset_script'
    id = Int(primary=True)
    last_duration = Int()
    idx = Int()
    buildset_id = Int()
    script_id = Int()

class build(Storm):
    __storm_table__ = 'build'
    id = Int(primary=True)
    scheduled_for = DateTime()
    start_time = DateTime()
    end_time = DateTime()
    work_dir = Unicode()
    info = Unicode()
    buildset_id = Int()
    
    @classmethod
    def createFromBuildset(cls, dbbuildset,  scheduled_for = None):
        """Create a new build using the buildset provided"""
        store = Store.of(dbbuildset)
        b = cls()
        b.buildset_id = dbbuildset.id
        
        if scheduled_for is None:
                scheduled_for = datetime.utcnow()
        b.scheduled_for = scheduled_for
        store.add(b)
        store.flush()
        
        # assign scripts to be build
        #print str(dbbuildset.buildset_scripts)
        for sp in dbbuildset.buildset_scripts:
            bp = build_script_status()
            bp.buildset_script_id = sp.id
            bp.build_id = b.id
            #print "%s %s" % (str(sp.script.name),  str(sp.idx))
            #print "%s" % str(sp.idx)
            #print str(sp.idx) 
            bp.idx = sp.idx
            store.add(bp)
        store.commit()
        return b

    def getDurations(self):
        """ Return a tuple of (duration, eta duration) """
        duration = 0
        eta_duration = 0
        store = Store.of(self)

        for status in self.build_script_statuses:
                start_time = status.start_time
                end_time = status.end_time or datetime.utcnow()
                if start_time:
                    duration += (end_time - start_time).seconds
        
                last = status.buildset_script.last_duration
                if last:
                    eta_duration += last

        return (duration, eta_duration)

class build_script_status(Storm):
    __storm_table__ = 'build_script_status'
    id = Int(primary=True)
    start_time = DateTime()
    end_time = DateTime()
    idx = Int()
    log = Unicode()
    exit_code = Int()
    buildset_script_id = Int()
    build_id = Int()

script.parent = Reference(script.parent_id, script.id)

buildset.buildset_scripts = ReferenceSet(buildset.id, buildset_script.buildset_id)
buildset_script.script = Reference(buildset_script.script_id, script.id)
buildset_script.buildset = Reference(buildset_script.buildset_id, buildset.id)

build.buildset = Reference(build.buildset_id, buildset.id)
build.build_script_statuses = ReferenceSet(build.id, build_script_status.build_id)

# build.build_scripts = ReferenceSet(build.id, build_script.build_id)
build_script_status.build = Reference(build_script_status.build_id, build.id)
build_script_status.buildset_script = Reference(build_script_status.buildset_script_id, buildset_script.id)
