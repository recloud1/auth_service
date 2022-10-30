from http import HTTPStatus
from json import JSONEncoder
from uuid import UUID

import click
from flask import Flask
from flask_jwt_extended import JWTManager

from core.config import envs
from core.constants import ROLES
from core.exceptions import ObjectNotExists, NoPermissionException, ObjectAlreadyExists, NotAuthorized, \
    LogicException
from core.swagger import api
from internal.users import user_crud
from models import User
from routes.auth import auth
from routes.roles import roles
from routes.users import users
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

app.register_blueprint(users)
app.register_blueprint(auth)
app.register_blueprint(roles)


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
    app.run(host=envs.app.host, port=envs.app.port)
