from flask import Flask

from core.config import envs
from core.swagger import swagger
from routes.auth import auth
from routes.example import example
from routes.roles import roles
from routes.users import users

app = Flask(__name__)

app.register_blueprint(users)
app.register_blueprint(auth)
app.register_blueprint(roles)
app.register_blueprint(example)

if __name__ == '__main__':
    swagger.register(app)
    app.run(host=envs.app.host, port=envs.app.port)
