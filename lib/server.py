import BaseHTTPServer
import simplejson as json
import db
from storm.locals import *
from datetime import datetime

_store = None
_app_root = None

class RequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    
    def do_GET(self):
        toks = self.path.split('?')
        path = toks[0]
        
        if path[0] == '/':
            path = path[1:].split('/')
        
        params = {}
        # Parse query params
        if len(toks) > 1:
            ps = toks[1].split('&')
            for i in ps:
                v = i.split('=')
                f = params.setdefault(v[0],  [])
                if len(v) > 1:
                    f.append(v[1])
                else:
                    f.append('')
                params[v[0]] = f
        
        cmds = { 'buildset' : self.getBuildSet,  
                 'script' : self.getScript, 
                 'builds.json' : self.getBuilds, 
                 'css' : self.wrenchApp, 
                 'app' : self.wrenchApp, 
                 'wrench' : self.wrenchApp, 
                 'json' : self.wrenchApp, 
                 'index.html' : self.wrenchApp,
                 'boot.js' : self.wrenchApp,
                 '' : self.wrenchApp
                 }
                    
        cmd = cmds.get(path[0])
        if not cmd:
            self.send_response(400)
            self.send_header('Content-type',        'text/html')
            self.end_headers()
            self.wfile.write("Unknown method")
        else:
            self.wfile.write(cmd(path,  params))
        
        #print "path %s" % str(path)
        #print " %s" % str(params)

    def getScript(self,  path,  params):
        self.send_response(200)
        self.send_header('Content-type',        'application/json')
        self.end_headers()
        return ""

    def getBuildSet(self, path,  params):
        self.send_response(200)
        self.send_header('Content-type',        'application/json')
        self.end_headers()

        # Just return a list of available stage ids -> name
        if len(path) == 1:
            s = _store.find(db.stage)
            res = {}
            for i in s:
                res[i.id] = i.name
            return json.dumps(res)
        
        # Return the stage requested and the associated packages
        id = int(path[1])
        
        s = _store.get(db.stage,  id)
        packs = [] 
        for j in s.stage_packages:
            i = j.package

            # Get the latest build version that matches this stage
            last_ver = _store.find(db.build_package, db.build_package.stage_package_id == i.id).order_by(Desc(db.build_package.id)).first();
            version = '0.0-0'
            revision = "HEAD"
            branch = "TRUNK"
            if last_ver:
                version = last.version
                #revision = last.revision
                #branch = last.branch
            
            packs.append( {'name' : i.name,  'id' : i.id,  'parent_id' : i.parent_id, 'last_version' : version,
                           'last_revision' : revision, 'last_branch' : branch})
        
        return json.dumps( { 'id' : id,  'name' : s.name,  'packages' : packs})
        
    def getBuilds(self, path,  params):
        """
        Return json like
        [
        { "id": 1, "name": "Name A", "start_time": "2010-01-19 15:10:00", "server_time" : "2010-01-19 15:13:00", 
	  "server" : "sdev1", "scripts":  
	 [ 
	 { "id":1, "est_duration": 20, "duration": 16, "state": "done", "name": "zecure-payment" },
         ...
         ],
         ...
        ]

        """

        self.send_response(200)
        self.send_header('Content-type',        'application/json')
        self.end_headers()

        time_fmt = '%Y-%m-%d %H:%M:%S'
        now = datetime.utcnow()
        server_time = now.strftime(time_fmt)

        # Return a list of all running and pending builds
        res = []
        builds = _store.find(db.build)
        for build in builds:

            res_build = { 'id' : build.id, 'name' : 'mybuild' }
            res_build['start_time'] = ( build.start_time and build.start_time.strftime(time_fmt) or
                                        build.scheduled_for.strftime(time_fmt) )
            res_build['server_time'] = server_time
            res_build['server'] = 'localhost'
            scripts = []
            res_build['scripts'] = scripts
            res.append(res_build)
            
            for script_status in build.build_script_statuses.order_by(db.build_script_status.start_time):
                
                name = script_status.buildset_script.script.getCanonicalName()
                est_duration = 30
                duration = 0
                state = "pending"

                if script_status.start_time:
                    state = "running"
                    duration = (now - script_status.start_time).seconds

                if script_status.end_time:
                    duration = (script_status.end_time - script_status.start_time).seconds

                    if script_status.exit_code:
                        state = "error"
                    else:
                        state = "ok"

                res_script = { 'id' : script_status.id, 'name' : name,
                               'state' : state, 'duration' : duration,
                               'est_duration' : est_duration }
                scripts.append(res_script)
                
        return json.dumps(res)
        
        # Return the stage requested and the associated packages
        id = int(path[1])
        
        s = _store.get(db.stage,  id)
        packs = [] 
        for j in s.stage_packages:
            i = j.package

            # Get the latest build version that matches this stage
            last_ver = _store.find(db.build_package, db.build_package.stage_package_id == i.id).order_by(Desc(db.build_package.id)).first();
            version = '0.0-0'
            revision = "HEAD"
            branch = "TRUNK"
            if last_ver:
                version = last.version
                #revision = last.revision
                #branch = last.branch
            
            packs.append( {'name' : i.name,  'id' : i.id,  'parent_id' : i.parent_id, 'last_version' : version,
                           'last_revision' : revision, 'last_branch' : branch})
        
        return json.dumps( { 'id' : id,  'name' : s.name,  'packages' : packs})

    def wrenchApp(self,  path, params):
        """Provider of the javascript files etc. for the wrench application"""
        if path[0] == '':
            path = ['index.html']
        try:
            c = open(_app_root + "/" + '/'.join(path),  'r').read()
        except:
            self.send_response(400)
            return ""

        self.send_response(200)
        if path[-1][-3:] == '.js':
            self.send_header('Content-type',        'text/plain')
        elif path[-1][-4:] == '.css':
            self.send_header('Content-type',        'text/css')
        else:
            self.send_header('Content-type',        'text/html')
        self.end_headers()

        print "providing " + _app_root + "/" + '/'.join(path)
        return c

def run(port,  store,  app_root):
    "Run a http server on the given port"
    global _store
    _store = store
    global _app_root
    _app_root = app_root 
    server_address = ('', port)
    httpd = BaseHTTPServer.HTTPServer(server_address, RequestHandler )
    httpd.serve_forever()
    
if __name__ == '__main__':
    run(8765)
    
