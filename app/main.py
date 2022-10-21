from flasgger import Swagger
from flask import Flask

from core.config import envs
from core.swagger import template
from routes.auth import auth
from routes.roles import roles
from routes.users import users

app = Flask(__name__)
app.config['FLASK_PYDANTIC_VALIDATION_ERROR_STATUS_CODE'] = 422

swagger = Swagger(app, template=template)

app.register_blueprint(users)
app.register_blueprint(auth)
app.register_blueprint(roles)

if __name__ == '__main__':
    app.run(host=envs.app.host, port=envs.app.port)
