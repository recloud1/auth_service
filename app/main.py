from flasgger import Swagger
from flask import Flask

from core.config import envs
from routes.auth import auth
from routes.roles import roles
from routes.users import users

app = Flask(__name__)
swagger = Swagger(app)

app.register_blueprint(users)
app.register_blueprint(auth)
app.register_blueprint(roles)

if __name__ == '__main__':
    app.run(host=envs.app.host, port=envs.app.port)
