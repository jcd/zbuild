from storm.locals import *
from layout import table_layout,  counter_length
import sys
from datetime import datetime

class stage(Storm):
    __storm_table__ = 'stage'
    id = Int(primary=True)
    name = Unicode()

    @classmethod
    def dumpNames(cls, store,  os):
        """
        Write all packages to outstream os
        """
        stages = store.find(cls).order_by(cls.id)
        counter_len = counter_length(stages.count())
        arr = [ ['idx ', 'name', ' duration'] ]
        idx = 0
        for stage in stages:
            dur = None # stages[i].metadata.get('duration',None)
            if dur:
                dur = ':'.join(str(dur).split(':')[1:])
            else:
                dur = "  -"
            arr2 = []
            arr2.append(str(idx).rjust(counter_len,'0'))
            arr2.append(stage.name)
            arr2.append(" %s" % (str(dur).split('.')[0],))
            arr.append(arr2)
            idx += 1
        os(table_layout(arr, True, "    "))
    
    def dumpPackageNames(self,  os):
            """
            write list of packages to logger
            """
            pks = Store.of(self).find(stage_package, stage_package.stage_id == self.id)
            packs = pks.order_by(Asc(stage_package.idx))
            counter_len = counter_length(packs.count())
            arr = [ ['idx ', 'name', ' duration'] ]
            idx = 0
            for pack in packs:
                packtime = None # i.metadata['timings'].get(i.name,None)
                dur = "  -"
                if packtime:
                    dut = packtime.get('duration')
                    if dur:
                        dur = ':'.join(str(dur).split(':')[1:])
                arr2 = []
                arr2.append(str(pack.idx).rjust(counter_len,'0'))
                arr2.append(pack.package.name)
                arr2.append(" %s" % (str(dur).split('.')[0],))
                arr.append(arr2)
                idx += 1
            os(table_layout(arr, True, "    "))
    
    @classmethod
    def getByIndex(cls, store,  idx):
        """
        Get stage by index
        """
        stages = store.find(cls).order_by(cls.id)
        curidx = 0
        for i in stages:
            if curidx == idx:
                return i
            curidx += 1
        return None
    
    @classmethod
    def getByName(cls,  store, name):
        return store.find(cls,  name == cls.name).one()
    
    @classmethod
    def getByIdent(cls,  store, ident):
        try:
            s = cls.getByIndex(store, int(ident))
            if s:
                return s
        except:
            pass
        return cls.getByName(store, ident)
        
    def getPackageIndex(self,  pack):
        """Return the index the given package has in this stage or None"""
        if type(pack) != package:
            return None
        for i in self.stage_packages:
            if i.package_id == pack.id:
                return i.idx
        return None
        
    def addPackage(self, pack,  before_package_idx = sys.maxint):
        """Add a new package to this stage"""
        idx = int(before_package_idx)
        store = Store.of(self)
        pks = store.find(stage_package, stage_package.stage_id == self.id)
        m = pks.max(stage_package.idx) 
        if m is None:
            # First package is added
            idx = 0
        elif m < idx:
            # append using m+1
            idx = m + 1
        
        # move all tasks with higher or equal index that idx one step
        opks = pks.order_by(Desc(stage_package.idx))
        for i in opks:
            if i.idx >= idx:
                i.idx += 1
        
        # Create new pack
        spack = stage_package()
        spack.stage_id = self.id
        spack.package_id = pack.id
        spack.idx = idx
            
        store.add(spack)
        store.commit()

    def removePackage(self,  pack):
        """Remove package from stage. Pack is eigther a db.package or an index"""
        idx = self.getPackageIndex(pack)
        if not idx:
            # pack is not a package instance in this stage, then it must be an index
            idx = int(pack)
            
        store = Store.of(self)
        pks = store.find(stage_package, stage_package.stage_id == self.id)
        opks = pks.order_by(Asc(stage_package.idx))
        # Correct idx for packs larger that the one removed
        for i in opks:
            if i.idx == idx:
                store.remove(i)
            elif i.idx > idx:
                i.idx -= 1
        store.commit()
            
class package(Storm):
    __storm_table__ = 'package'
    id = Int(primary=True)
    name = Unicode()
    path = Unicode()
    parent_id = Int()
    
    @classmethod
    def dumpNames(cls, store,  os):
        """
        Write all packages to outstream os
        """
        idx = 0
        packs = store.find(cls).order_by(cls.id)
        counter_len = counter_length(packs.count())
        arr = [ ['idx ','name',' duration'] ]
        
        for pack in packs:
            dur = None # pack.metadata.get('duration',None)
            if dur:
                dur = ':'.join(str(dur).split(':')[1:])
            else:
                dur = "  -"
            arr2 = []
            arr2.append(str(idx).rjust(counter_len,'0'))
            arr2.append(pack.name)
            arr2.append(" %s" % (str(dur).split('.')[0],))
            arr.append(arr2)
            idx += 1
        os(table_layout(arr, True, "    "))

    @classmethod
    def getByIndex(cls, store,  idx):
        """
        Get stage by index
        """
        packs = store.find(cls).order_by(cls.id)
        curidx = 0
        for i in packs:
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
        

class stage_package(Storm):
    __storm_table__ = 'stage_package'
    id = Int(primary=True)
    last_duration = DateTime()
    idx = Int()
    stage_id = Int()
    package_id = Int()

class build(Storm):
    __storm_table__ = 'build'
    id = Int(primary=True)
    scheduled_for = DateTime()
    start_time = DateTime()
    end_time = DateTime()
    work_dir = Unicode()
    info = Unicode()
    stage_id = Int()
    
    @classmethod
    def createFromStage(cls, dbstage,  scheduled_for = None):
        """Create a new build using the stage provided"""
        store = Store.of(dbstage)
        b = cls()
        b.stage_id = dbstage.id
        
        if scheduled_for is None:
                scheduled_for = datetime.utcnow()
        b.scheduled_for = scheduled_for
        store.add(b)
        store.flush()
        
        # assign packages to be build
        for sp in dbstage.stage_packages:
            bp = build_package()
            bp.stage_package_id = sp.id
            bp.build_id = b.id
            print "%s %i" % (sp.package.name,  sp.idx)
            print str(sp.idx) 
            bp.idx = sp.idx
            store.add(bp)
        store.commit()
        return b
        
class build_package(Storm):
    __storm_table__ = 'build_package'
    id = Int(primary=True)
    start_time = DateTime()
    end_time = DateTime()
    idx = Int()
    log = Unicode()
    stage_package_id = Int()
    build_id = Int()

package.parent = Reference(package.id, package.parent_id)

stage.stage_packages = ReferenceSet(stage.id, stage_package.stage_id)
stage_package.package = Reference(stage_package.package_id,  package.id)
stage_package.stage = Reference(stage.id, stage_package.id)

build.stage = Reference(build.stage_id,  stage.id)
build.build_packages = ReferenceSet(build.id, build_package.build_id)
build_package.build = Reference(build.id, build_package.build_id)
build_package.stage_package = Reference(build_package.stage_package_id, stage_package.id)
