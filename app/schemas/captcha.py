from schemas.core import Model


class CaptchaIn(Model):
    data: str


class CaptchaOut(Model):
    data: str
    message: str
