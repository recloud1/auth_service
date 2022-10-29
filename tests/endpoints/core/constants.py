import enum


class RequestMethods(str, enum.Enum):
    get = 'GET'
    post = 'POST'


class ApiRoutes(str, enum.Enum):
    auth = 'auth'
    roles = 'roles'
    users = 'users'
