from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from spectree import Response

from core.exceptions.default_messages import ExceptionMessages
from core.exceptions.exceptions import LogicException
from core.swagger import api
from internal.captcha import captcha_service
from routes.core import responses
from schemas.captcha import CaptchaOut, CaptchaIn
from schemas.core import StatusResponse
from utils.auth import get_ip_address_from_request

captcha = Blueprint(name='captcha', import_name=__name__, url_prefix='/v1/captcha')
route_tags = ['Captcha']


@captcha.get('/')
@api.validate(resp=Response(HTTP_200=CaptchaOut, **responses), tags=route_tags)
@jwt_required()
def generate_captcha():
    ip_addr = get_ip_address_from_request(request)
    problem = captcha_service.generate_problem(key=ip_addr)

    return CaptchaOut(data=problem, message='Вы проявляете подозрительную активность!')


@captcha.post('/')
@api.validate(resp=Response(HTTP_200=StatusResponse, **responses), tags=route_tags)
@jwt_required()
def validate_captcha(json: CaptchaIn):
    ip_addr = get_ip_address_from_request(request)

    if not captcha_service.check_value(key=ip_addr, value=json.data):
        raise LogicException(ExceptionMessages.captcha_not_valid())

    captcha_service.unblock(ip_addr)

    return StatusResponse()
