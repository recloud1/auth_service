from flask import Request
from passlib.handlers.pbkdf2 import pbkdf2_sha512

from core.constants import IP_HEADER_PARAM


def generate_password_hash(password: str) -> str:
    """
    Создаёт хэш пароля для хранения в БД
    """
    return pbkdf2_sha512.hash(password)


def verify_password(input_password: str, password_hash: str) -> bool:
    """
    Сравнивает полученный вариант пароля с захэшированным вариантом
    """
    return pbkdf2_sha512.verify(input_password, password_hash)


def get_token_from_headers(headers: dict):
    """
    Достает JWT-токен из блока Header HTTP-запроса
    """
    return headers['Authorization'].split(' ')[-1]


def get_ip_address_from_request(request: Request) -> str:
    """
    Достает ip-адрес из параметров запроса
    """
    ip_addr = request.environ.get(IP_HEADER_PARAM, request.remote_addr)
    return ip_addr
