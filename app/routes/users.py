from flask import Blueprint

users = Blueprint(name='users', import_name=__name__, url_prefix='/users')
