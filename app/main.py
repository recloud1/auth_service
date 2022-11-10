from http import HTTPStatus
from json import JSONEncoder
from uuid import UUID

import click
from flask import Flask, request
from flask_jwt_extended import JWTManager

from core.config import envs
from core.constants import ROLES, REQUEST_HEADER_ID
from core.exceptions.default_messages import request_id_necessary_msg
from core.exceptions.exceptions import LogicException, NotAuthorized, ObjectAlreadyExists, ObjectNotExists, \
    NoPermissionException
from core.swagger import api
from core.tracer import configure_tracer
from internal.users import user_crud
from models import User
from routes.v1.auth import auth
from routes.v1.oauth import oauth
from routes.v1.roles import roles
from routes.v1.users import users
from schemas.core import ErrorSchema
from schemas.users import UserCreate
from utils.db import db_session_manager

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

if envs.tracer.enable:
    configure_tracer(app, envs.tracer.host, envs.tracer.port)

app.register_blueprint(users)
app.register_blueprint(auth)
app.register_blueprint(roles)
app.register_blueprint(oauth)


@app.errorhandler(LogicException)
def handle_error(e):
    return ErrorSchema(detail=str(e)).dict(), HTTPStatus.BAD_REQUEST


@app.errorhandler(NotAuthorized)
def handle_error(e):
    return ErrorSchema(detail=str(e)).dict(), HTTPStatus.UNAUTHORIZED


@app.errorhandler(ObjectAlreadyExists)
def handle_error(e):
    return ErrorSchema(detail=str(e)).dict(), HTTPStatus.CONFLICT


@app.errorhandler(ObjectNotExists)
def handle_error(e):
    return ErrorSchema(detail=str(e)).dict(), HTTPStatus.NOT_FOUND


@app.errorhandler(NoPermissionException)
def handle_error(e):
    return ErrorSchema(detail=str(e)).dict(), HTTPStatus.FORBIDDEN


@app.before_request
def before_request():
    request_id = request.headers.get(REQUEST_HEADER_ID)
    if not request_id and not envs.app.debug:
        raise RuntimeError(request_id_necessary_msg)


@click.command(name='create-superuser')
@click.option('--login', prompt='Введите логин суперпользователя', help='Логин суперпользователя')
@click.option('--password', prompt='Введите пароль суперпользователя', help='Пароль суперпользователя')
def create_user(login: str, password: str):
    superuser = UserCreate(
        login=login,
        email='superuser@notmail.com',
        password=password,
        role_id=ROLES.root.value
    )

    with db_session_manager() as session:
        existing_user_query = session.query(User).where(User.login == login, User.role_id == ROLES.root.value)
        existing_user: User = session.scalar(existing_user_query)
        if existing_user:
            print('Superuser with the same login already exists! Try pass the another login')
        else:
            user_crud.create(session, superuser)


if __name__ == '__main__':
    api.register(app)
    app.run(host='0.0.0.0', port=envs.app.port, debug=envs.app.debug)
