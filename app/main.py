from core.config import envs
from core.exceptions import ObjectNotExists, NoPermissionException, ObjectAlreadyExists
from core.swagger import api
from flask import Flask, jsonify
from routes.auth import auth
from routes.roles import roles
from routes.users import users

app = Flask(__name__)

app.register_blueprint(users)
app.register_blueprint(auth)
app.register_blueprint(roles)


@app.errorhandler(ObjectAlreadyExists)
def handle_error(e):
    return jsonify(str(e)), 409


@app.errorhandler(ObjectNotExists)
def handle_error(e):
    return jsonify(str(e)), 404


@app.errorhandler(NoPermissionException)
def handle_error(e):
    return jsonify(str(e)), 403


if __name__ == '__main__':
    api.register(app)
    app.run(host=envs.app.host, port=envs.app.port)
