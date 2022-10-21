import datetime
import uuid
from typing import List

from models.core import Base, TimestampMixin, fresh_timestamp
from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


class Role(Base, TimestampMixin):
    __repr_name__ = 'Роль'
    __tablename__ = 'roles'
    __table_args__ = {'schema': 'roles'}

    id: int = Column(UUID, primary_key=True, server_default=str(uuid.uuid4()))
    name: str = Column(String(256), nullable=False)
    description: str = Column(String(256), nullable=True)

    permissions: List['RolePermission'] = relationship('RolePermission')


class RolePermission(Base):
    __repr_name__ = 'Разрешения роли'
    __tablename__ = 'role_permissions'
    __table_args__ = {'schema': 'roles'}

    id: int = Column(UUID, primary_key=True, server_default=str(uuid.uuid4()))
    permission: str = Column(String(512), nullable=False, unique=True)
    role_id: int = Column(UUID, ForeignKey('roles.roles.id'), nullable=False, index=True)

    created_by: str = Column(UUID)

    created_at: datetime.datetime = Column(DateTime, default=fresh_timestamp())
    updated_at: datetime.datetime = Column(DateTime, default=fresh_timestamp(), onupdate=fresh_timestamp())
