import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from models import Base, Role, TimestampMixin, fresh_timestamp


class User(TimestampMixin, Base):
    __repr_name__ = 'Пользователь'
    __tablename__ = 'users'
    __table_args__ = {'schema': 'users'}

    id: str = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_id: str = Column(UUID(as_uuid=True), ForeignKey('roles.roles.id'), nullable=False)

    login = Column(String(128), nullable=False, unique=True)
    email = Column(String(256), nullable=True, unique=True)
    password = Column(String(256), nullable=True)

    first_name: str = Column(Text, nullable=True)
    last_name: str = Column(Text, nullable=True)
    middle_name: str = Column(Text, nullable=True)

    role: 'Role' = relationship('Role', uselist=False)

    @hybrid_property
    def role_name(self) -> str:
        return self.role.name


class UserLoginHistory(Base):
    __repr_name__ = 'История посещений пользователя'
    __tablename__ = 'user_login_histories'
    __table_args__ = {'schema': 'users'}

    id: str = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: str = Column(
        UUID(as_uuid=True),
        ForeignKey('users.users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    ip: str = Column(Text)
    fingerprint: dict = Column(JSONB)
    created_at = Column(DateTime, default=fresh_timestamp())

    user: 'User' = relationship('User')


class UserSocialAccount(Base):
    __repr_name__ = 'Аккаунт пользователя заведенный через социальные сети'
    __tablename__ = 'user_social_accounts'
    __table_args__ = ((UniqueConstraint('social_id', 'social_name', name='unique_social_pk')),
                      {'schema': 'users'})

    id: str = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id: str = Column(
        UUID(as_uuid=True),
        ForeignKey('users.users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    social_id: str = Column(Text, nullable=False)
    social_name: str = Column(Text, nullable=False)

    created_at = Column(DateTime, default=fresh_timestamp())
    deleted_at = Column(DateTime, nullable=True)

    user: 'User' = relationship('User')
