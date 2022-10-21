from flask import Blueprint, request, jsonify
from flask_pydantic_spec import Request, Response
from pydantic import constr, Field

from core.swagger import swagger
from schemas.core import Model

example = Blueprint(name='example', import_name=__name__, url_prefix='/example')


class Profile(Model):
    name: constr(min_length=2, max_length=40)
    age: int = Field(
        ...,
        gt=0,
        lt=150,
        description='user age(Human)'
    )

    class Config:
        schema_extra = {
            'example': {
                'name': 'very_important_user',
                'age': 42,
            }
        }


class Message(Model):
    text: str


@example.route('', methods=['POST'])
@swagger.validate(body=Request(Profile), resp=Response(HTTP_200=Profile, HTTP_403=None), tags=['TAG'])
def echo():
    """
    Шорт-дескришн роута

    Более детальная информация о работе роута
    """
    result = request.json
    return result
