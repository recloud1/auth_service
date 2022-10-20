import logging


def set_logging(
        log_level: str = logging.DEBUG,
        enable_additional_debug: bool = True
) -> None:
    """
    Установка конфигурация для логирования приложения.

    Необходимо вызвать как можно раньше.

    :param log_level: уровень выводимых логов
    :param enable_additional_debug: выводить ли информации из сторонних библиотек
    """
    configure_logging(enable_additional_debug=enable_additional_debug)

    logging.basicConfig(
        level=log_level,
        force=True,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def configure_logging(enable_additional_debug=True):
    """
    Отключает дебаг информацию для библиотек, при необходимости

    :param enable_additional_debug: флаг включения логирования внешних библиотек
    """
    while len(logging.root.handlers) > 0:
        logging.root.removeHandler(logging.root.handlers[-1])

    get_logger('AdditionalDebug').info('enabled')

    # TODO: добавить возможность отключать дебаг библиотек
    if not enable_additional_debug:
        pass


def get_logger(logger_name: str):
    """
    Получение нового объекта логгера
    :param logger_name: наименование логгера
    """
    return logging.getLogger(logger_name)
