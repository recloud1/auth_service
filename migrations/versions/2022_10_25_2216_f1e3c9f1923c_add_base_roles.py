"""add_base_roles

Revision ID: f1e3c9f1923c
Revises: 767c1a72f4e7
Create Date: 2022-10-25 22:16:07.563161

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
from migrations.versions.data_versions.data_2022_10_25_2216_f1e3c9f1923c_add_base_roles import data_upgrade, \
    data_downgrade

revision = 'f1e3c9f1923c'
down_revision = '767c1a72f4e7'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        'role_permissions', 'created_by',
        existing_type=postgresql.UUID(),
        nullable=False,
        schema='roles'
    )
    op.create_foreign_key(
        op.f('fk_role_permissions_created_by_users'),
        'role_permissions',
        'users',
        ['created_by'],
        ['id'],
        source_schema='roles',
        referent_schema='users'
    )

    data_upgrade(op)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    data_downgrade(op)

    op.drop_constraint(
        op.f('fk_role_permissions_created_by_users'),
        'role_permissions',
        schema='roles',
        type_='foreignkey'
    )
    op.alter_column(
        'role_permissions', 'created_by',
        existing_type=postgresql.UUID(),
        nullable=True,
        schema='roles'
    )

    # ### end Alembic commands ###
