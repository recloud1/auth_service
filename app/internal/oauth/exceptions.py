from core.exceptions import NotAuthorized


class OAuthException(NotAuthorized):
    """
    Проблемы при взаимодействии с OAuth-провайдером
    """

    def __init__(self, message: str, *args):
        super().__init__(message, *args)
