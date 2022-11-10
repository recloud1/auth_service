class ExceptionTextElement:
    """ Класс для хранения описаний Exceptions, которые выбрасываются в системе """

    def __init__(self, message: str, name: str | None = None):
        self.message = message
        self.name = name

    def __call__(self):
        return self.message


class ExceptionMessages:
    """ Текстовое описание ошибок системы """

    object_not_exists = ExceptionTextElement(message='Запись не найдена')
    object_already_exists = ExceptionTextElement(message='Запись с такими атрибутами уже существует')
    logic = ExceptionTextElement(message='Ошибка логики')

    no_permission = ExceptionTextElement(
        message='Пользователь не имеет достаточно прав для выполнения данного действия'
    )

    incorrect_data = ExceptionTextElement(message='Неверный логин или пароль')
    incorrect_token = ExceptionTextElement(message='Неверный токен авторизации')
    expired_token = ExceptionTextElement(
        message='Ваш токен более недействителен, пожалуйста авторизуйтесь снова'
    )
    blocked_account = ExceptionTextElement(
        message='Ваша учётная запись заблокирована. О причинах вы можете узнать у тех. поддержки'
    )
    two_auth_necessary = ExceptionTextElement(message='Вам необходимо пройти двухфакторную аутентификацию')
    two_auth_already_exists = ExceptionTextElement(message='Двухфакторная аутентификация уже подключена')
    two_auth_code_not_valid = ExceptionTextElement(message='Введенный код неверен')
    request_id_necessary = ExceptionTextElement(
        message='Request Id - обязательный параметр при выполнение запроса'
    )
    too_many_requests = ExceptionTextElement(message='Too Many Requests')
