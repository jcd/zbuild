from lib import db

def server(args):
    store = db.initdb()

    server.run(OPTIONS.port,  store,  OPTIONS.zbuild_install_dir + "/gui")
