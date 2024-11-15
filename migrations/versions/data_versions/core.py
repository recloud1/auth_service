from typing import List, Tuple, Iterable

import sqlalchemy as sa


class DataMigration:
    def __init__(self, insert_query, delete_query, values: List[dict], **global_params):
        self._check_values(values)
        self.values = values
        self.delete_query = delete_query
        self.insert_query = insert_query

        self.global_params = global_params

    @staticmethod
    def _check_values(values: List[dict]):
        return
        # TODO подумать о необходимости
        for value in values:
            if value.get('id') is None:
                raise ValueError(f"All data migration values should have the id. Got: {value}")

    def insert(self, connection: sa.engine.Connection):
        for value in self.values:
            connection.execute(sa.text(self.insert_query), {**value, **self.global_params})

    def delete(self, connection: sa.engine.Connection):
        for value in self.values:
            connection.execute(sa.text(self.delete_query), {**value, **self.global_params})


class GeneratingMigration(DataMigration):
    def __init__(
            self, table_name: str, values: List[dict], move_sequence=True, sequence_name: str = None,
            delete_by_fields: Tuple[str, ...] = ('id',), **global_params
    ):

        self.global_params = global_params
        self._check_values(values)

        self.check_delete_key_persist(delete_by_fields, values)
        self.delete_by_fields = delete_by_fields

        self.sequence_query = self.build_sequence_query(table_name, sequence_name)

        insert_query = self.build_insert_query(table_name, values)
        delete_query = self.build_delete_query(table_name, values)

        super().__init__(insert_query, delete_query, values, **global_params)

        self.move_sequence = move_sequence
        self.table_name = table_name

    def check_delete_key_persist(self, checking: Iterable[str], values: List[dict]):
        persist_keys = self.collect_keys(values)
        for check in checking:
            if check not in persist_keys:
                raise ValueError('Delete fields should be specified in all values')

    def build_insert_query(self, table_name: str, values: List[dict]):
        keys = ", ".join(self.collect_keys(values))
        # :var_name – стандартный синтаксис вставки значений для sqlalchemy
        mapping = ", ".join([':' + i for i in self.collect_keys(values)])
        insert_query = f'INSERT INTO {table_name} ({keys}) VALUES ({mapping})'

        return insert_query

    @staticmethod
    def build_sequence_query(table_name: str, sequence_name: str):
        sequence_name = f'{table_name}_id_seq' if sequence_name is None else sequence_name
        query = f"SELECT setval('{sequence_name}',COALESCE((SELECT MAX(id)+1 FROM {table_name}), 1), false)"

        return query

    def build_delete_query(self, table_name: str, values: List[dict]):
        keys = sorted(self.delete_by_fields)
        filter_condition = ' AND '.join([f'{i}=:{i}' for i in keys])

        delete_query = f'DELETE FROM {table_name} WHERE {filter_condition}'
        return delete_query

    def collect_keys(self, values: List[dict]) -> List[str]:
        keys = set()
        for v in values:
            for key in v.keys():
                keys.add(key)

        for global_key in self.global_params:
            keys.add(global_key)

        return sorted(keys)

    def insert(self, connection: sa.engine.Connection):
        super().insert(connection)
        if self.move_sequence:
            connection.execute(self.sequence_query)
