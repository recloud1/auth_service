import contextlib
from contextvars import ContextVar
from typing import Callable, ContextManager, Generator, Tuple

from core.config import envs
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

session_context: ContextVar[Session] = ContextVar('session_context')


def session_factory(
        connection_string,
        **engine_params
) -> Tuple[Generator[Session, None, None], Callable[[], ContextManager[Session]], Engine]:
    """
    Функция для создания фабрики соединений с бд

    :param connection_string: параметры для подключения к БД
    :param engine_params: параметры для Engine (настройки пула соединений)
    :return: генератор для использования в fastapi.Depends, контекстный менеджер
             бд для использования в любом ином месте, Engine для низкоуровнего взаимодействия
    """
    engine = create_engine(connection_string, **engine_params)
    Session = sessionmaker(bind=engine)

    def get_session() -> Generator[Session, None, None]:
        try:
            sess: Session = Session()
            session_context.set(sess)
            yield sess
        except Exception as e:
            sess.rollback()
            raise e
        finally:
            sess.commit()
            sess.close()

    return get_session, contextlib.contextmanager(get_session), engine


db_session, db_session_manager, engine = session_factory(envs.db.connection_string)
