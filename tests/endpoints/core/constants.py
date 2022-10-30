import enum


class RequestMethods(str, enum.Enum):
    get = 'GET'
    post = 'POST'


class ApiRoutes(str, enum.Enum):
    auth = 'v1/auth'
    roles = 'v1/roles'
    users = 'v1/users'
