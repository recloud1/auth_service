import uuid

from models import Base, Role, TimestampMixin, fresh_timestamp
from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship


class User(TimestampMixin, Base):
    __repr_name__ = 'Пользователь'
    __tablename__ = 'users'
    __table_args__ = {'schema': 'users'}

    id: int = Column(UUID, primary_key=True, server_default=str(uuid.uuid4()))
    role_id: str = Column(UUID, ForeignKey('roles.roles.id'), nullable=False)

    login = Column(String(128), nullable=True, unique=True)
    email = Column(String(256), nullable=False, unique=True)
    password = Column(String(256), nullable=False)

    first_name: str = Column(Text, nullable=True)
    last_name: str = Column(Text, nullable=True)
    middle_name: str = Column(Text, nullable=True)

    role: 'Role' = relationship('Role', uselist=False)
    # allowed_devices: List['UserAllowedDevice'] = relationship('UserAllowedDevice', uselist=True)


class UserLoginHistory(Base):
    __repr_name__ = 'История посещений пользователя'
    __tablename__ = 'user_login_histories'
    __table_args__ = {'schema': 'users'}

    id: int = Column(UUID, primary_key=True, server_default=str(uuid.uuid4()))
    user_id: str = Column(UUID, ForeignKey('users.users.id', ondelete='CASCADE'), nullable=False, index=True)
    ip: str = Column(Text)
    fingerprint: dict = Column(JSONB)
    created_at = Column(DateTime, default=fresh_timestamp())

    user: 'User' = relationship('User')


# class UserAllowedDevice(Base):
#     __repr_name__ = 'Разрешенные пользователем устройства для входа'
#     __tablename__ = 'user_allowed_devices'
#     __table_args__ = {'schema': 'users'}

    # id: str = Column(UUID, primary_key=True)
