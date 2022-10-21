from sqlalchemy.orm import joinedload

from core.crud.base import CRUDPaginated
from models import User, UserLoginHistory

user_crud = CRUDPaginated(model=User, get_options=[joinedload(User.role)])

user_login_history_crud = CRUDPaginated(model=UserLoginHistory)
