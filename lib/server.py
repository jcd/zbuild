import BaseHTTPServer
import simplejson as json
import db
from storm.locals import *

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
        
        cmds = { 'stage' : self.getStage,  
                        'package' : self.getPackage, 
                        'css' : self.wrenchApp, 
                        'app' : self.wrenchApp, 
                        'wrench' : self.wrenchApp, 
                        'index.html' : self.wrenchApp, 
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

    def getPackage(self,  path,  params):
        self.send_response(200)
        self.send_header('Content-type',        'application/json')
        self.end_headers()
        return ""

    def getStage(self, path,  params):
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
        
    def wrenchApp(self,  path, params):
        """Provider of the javascript files etc. for the wrench application"""
        c = open(_app_root + "/" + '/'.join(path),  'r').read()

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
    
