from json import JSONEncoder
from uuid import UUID

from flask import Flask
from flask_jwt_extended import JWTManager

from core.config import envs
from core.exceptions import ObjectNotExists, NoPermissionException, ObjectAlreadyExists, NotAuthorized, \
    LogicException
from routes.auth import auth
from routes.roles import roles
from routes.users import users
from schemas.core import ErrorSchema

old_default = JSONEncoder.default


def new_default(self, obj):
    if isinstance(obj, UUID):
        return str(obj)
    return old_default(self, obj)


JSONEncoder.default = new_default

app = Flask(__name__)

app.config['JWT_SECRET_KEY'] = envs.token.secret
app.config['JWT_TOKEN_LOCATION'] = 'headers'
app.config['JWT_HEADER_NAME'] = 'Authorization'
app.config['JWT_HEADER_TYPE'] = 'Bearer'
jwt = JWTManager(app)

app.register_blueprint(users)
app.register_blueprint(auth)
app.register_blueprint(roles)


@app.errorhandler(LogicException)
def handle_error(e):
    return ErrorSchema(detail=str(e)).dict(), 400


@app.errorhandler(NotAuthorized)
def handle_error(e):
    return ErrorSchema(detail=str(e)).dict(), 401


@app.errorhandler(ObjectAlreadyExists)
def handle_error(e):
    return ErrorSchema(detail=str(e)).dict(), 409


@app.errorhandler(ObjectNotExists)
def handle_error(e):
    return ErrorSchema(detail=str(e)).dict(), 404


@app.errorhandler(NoPermissionException)
def handle_error(e):
    return ErrorSchema(detail=str(e)).dict(), 403


if __name__ == '__main__':
    # api.register(app)
    app.run(host=envs.app.host, port=envs.app.port)
