"""add_base_roles

Create Date: 2022-10-25 22:16:07.555985

"""

revision = ('767c1a72f4e7',)

from typing import Tuple

import sqlalchemy as sa

from .core import DataMigration, GeneratingMigration

# Please, write your values here
data: Tuple[DataMigration, ...] = (
    GeneratingMigration(
        'roles.roles',
        values=[
            {
                'id': '708db765-8122-48aa-be17-7b00f77541de',
                'name': 'root'
            },
            {
                'id': 'd6354fb4-d27a-4656-8cf2-ecbd9962b129',
                'name': 'user'
            },
            {
                'id': '397427ed-b15a-4e29-8170-c7e941817201',
                'name': 'administrator'
            },
        ],
        move_sequence=False
    ),
)


def data_upgrade(op):
    connection: sa.engine.Connection = op.get_bind()

    # default creation for data
    for value_set in data:
        value_set.insert(connection)


def data_downgrade(op):
    connection: sa.engine.Connection = op.get_bind()

    # default deletion for data
    for value_set in data:
        value_set.delete(connection)
