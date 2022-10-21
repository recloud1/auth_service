from core.config import envs
from core.swagger import api
from flask import Flask
from routes.auth import auth
from routes.roles import roles
from routes.users import users

app = Flask(__name__)

app.register_blueprint(users)
app.register_blueprint(auth)
app.register_blueprint(roles)

if __name__ == '__main__':
    api.register(app)
    app.run(host=envs.app.host, port=envs.app.port)
