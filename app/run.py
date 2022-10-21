from core.config import envs
from gevent import monkey
from gevent.pywsgi import WSGIServer

monkey.patch_all()


from main import app

http_server = WSGIServer(('0.0.0.0', envs.app.port), app)
http_server.serve_forever()
