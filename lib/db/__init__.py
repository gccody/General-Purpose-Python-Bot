import re
from sqlite3 import Connection, Cursor, connect, Error
from typing import List, Dict, Optional

from lib.progress import Progress


class Get:
    def __init__(self, parent):
        self.parent = parent
        self._table_names = [list(table["table"].keys())[0] for table in parent.table_info]

    def __getattribute__(self, name):
        table_names = super().__getattribute__('_table_names')
        if name in table_names:
            _get_rows = super().__getattribute__('_get_rows')
            return lambda **kwargs: _get_rows(name, **kwargs)
        return super().__getattribute__(name)

    def _get_rows(self, table_name: str, count: Optional[int] = None, **kwargs: Dict) -> List[object]:
        if not kwargs:
            query = f"SELECT * FROM {table_name}"
        else:
            query = f"SELECT * FROM {table_name} WHERE "
            query += " AND ".join([f"{key}='{value}'" for key, value in kwargs.items()])
        if count:
            query += f" LIMIT {count}"
            self.parent.cur.execute(query)
        rows = self.parent.cur.fetchall()
        for table in self.parent.table_info:
            if list(table["table"].keys())[0] == table_name:
                keys = list(table["table"][table_name].keys())
                class_name = table_name
                row_class = type(class_name, (object,), {})
                return [self._create_row(row_class, keys, row) for row in rows]

    def _create_row(self, row_class, keys, row):
        new_row = row_class()
        for i in range(len(keys)):
            setattr(new_row, keys[i], row[i])
        return new_row


class Delete:
    def __init__(self, parent):
        self.parent = parent
        self._table_names = [list(table["table"].keys())[0] for table in parent.table_info]

    def __getattribute__(self, name):
        table_names = super().__getattribute__('_table_names')
        if name in table_names:
            _delete_rows = super().__getattribute__('_delete_rows')
            return lambda **kwargs: _delete_rows(name, **kwargs)
        return super().__getattribute__(name)

    def _delete_rows(self, table_name, **kwargs):
        if not kwargs:
            raise ValueError("You must provide at least one argument to delete a row.")
        else:
            query = f"DELETE FROM {table_name} WHERE "
            query += " AND ".join([f"{key}='{value}'" for key, value in kwargs.items()])
            self.parent.cur.execute(query)
        self.parent.cxn.commit()


class Update:
    def __init__(self, parent):
        self.parent = parent
        self._table_names = [list(table["table"].keys())[0] for table in parent.table_info]

    def __getattribute__(self, name):
        table_names = super().__getattribute__('_table_names')
        if name in table_names:
            _update_rows = super().__getattribute__('_update_rows')
            return lambda **kwargs: _update_rows(name, **kwargs)
        return super().__getattribute__(name)

    def _update_rows(self, table_name, where, set_data):
        query = f"UPDATE {table_name} SET "
        query += ",".join([f"{key}='{value}'" for key, value in set_data.items()])
        query += f" WHERE {where}"
        self.parent.cur.execute(query)
        self.parent.cxn.commit()


class Insert:
    def __init__(self, parent):
        self.parent = parent
        self._table_names = [list(table["table"].keys())[0] for table in parent.table_info]

    def __getattribute__(self, name):
        table_names = super().__getattribute__('_table_names')
        if name in table_names:
            _insert_row = super().__getattribute__('_insert_row')
            return lambda **kwargs: _insert_row(name, **kwargs)
        return super().__getattribute__(name)

    def _insert_row(self, table_name, **kwargs):
        not_null_keys = [table["constraints"].get("not_null", []) for table in self.parent.table_info if list(table["table"].keys())[0] == table_name][0]
        for key in not_null_keys:
            if key not in kwargs:
                raise ValueError(f"Missing not null key '{key}'")
            elif kwargs[key] is None:
                raise ValueError(f"Key '{key}' is None")
        keys = [key for key in kwargs.keys()]
        values = [kwargs[key] for key in keys]
        query = f"INSERT INTO {table_name} ({','.join(keys)}) VALUES ({', '.join(['?' for _ in range(len(keys))])})"
        self.parent.cur.execute(query, tuple(values))
        self.parent.cxn.commit()


class DB:
    DB_PATH = "./data/database.db"
    cxn: Connection
    cur: Cursor
    table_info: List[Dict[str, Dict[str, Dict[str, str | List[str]]]]]
    table_names: List[str]

    table_info: list[dict[str, dict[str, dict[str, str | list[str]]]]] = [
        {
            'table': {
                'guilds': {
                    'id': 'TEXT',
                    'level_id': 'TEXT',
                    'announce_id': 'TEXT'
                }
            },
            'constraints': {'not_null': ['id'], 'primary_key': 'id'}
        },
        {
            'table': {
                'bans': {
                    'guild_id': 'TEXT',
                    'user_id': 'TEXT',
                    'mod_id': 'TEXT',
                    'reason': 'TEXT',
                    'ts': 'INTEGER'
                }
            },
            'constraints': {'foreign_key': {
                'guild_id': ['guilds', 'id']
            }}
        },
        {
            'table': {
                'reports': {
                    'guild_id': 'TEXT',
                    'user_id': 'TEXT',
                    'target_id': 'TEXT',
                    'report': 'TEXT'
                }
            },
            'constraints': {}
        },
        {
            'table': {
                'commands': {
                    'command_name': 'TEXT',
                    'guild_id': 'TEXT',
                    'user_id': 'TEXT',
                    'params': 'JSON',
                    'ts': 'INTEGER'
                }
            },
            'constraints': {}
        },
        {
            'table': {
                'levels': {
                    'guild_id': 'TEXT',
                    'user_id': 'TEXT',
                    'xp': 'INTEGER'
                }
            },
            'constraints': {}
        },
        {
            'table': {
                'youtube': {
                    'handle': 'TEXT',
                    'guild_id': 'TEXT',
                    'message': 'TEXT',
                    'latest_url': 'TEXT'
                }
            },
            'constraints': {}
        }
    ]

    table_names: list[str] = []

    def __init__(self):
        self.cxn = connect(self.DB_PATH, check_same_thread=False)
        self.cur = self.cxn.cursor()
        self.get: Get = Get(self)
        self.delete: Delete = Delete(self)
        self.update: Update = Update(self)
        self.insert: Insert = Insert(self)

    def update_table(self, table: str, data: str):
        try:
            self.cur.execute(f"SELECT * FROM {table}_new")
            self.cur.execute(f"INSERT INTO {table} SELECT * FROM {table}_new")
            self.cur.execute(f"DROP TABLE {table}_new")
        except Error:
            pass
        self.cur.execute(f"CREATE TABLE {table}_new {data};")
        self.cur.execute(f"INSERT INTO {table}_new SELECT * FROM {table};")
        self.cur.execute(f"DROP TABLE {table};")
        self.cur.execute(f"ALTER TABLE {table}_new RENAME TO {table};")

    def build(self) -> None:
        progress = Progress("Building Database", len(self.table_info))
        for table in self.table_info:
            table_data = table['table']
            for table_name, columns in table_data.items():
                self.table_names.append(table_name)
                create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name}("
                constraints = table.get('constraints')
                for column_name, data_type in columns.items():
                    if constraints:
                        not_null = constraints.get('not_null')
                        if not_null:
                            if column_name in not_null:
                                data_type += f" NOT NULL"
                    create_table_query += f"{column_name} {data_type}, "
                if constraints:
                    primary_key = constraints.get('primary_key')
                    default = constraints.get('default')
                    if default:
                        for column, value in default:
                            create_table_query += f"{column} DEFAULT {value}, "
                    if primary_key:
                        create_table_query += f"PRIMARY KEY({primary_key}), "
                    unique = constraints.get('unique')
                    if unique:
                        for column in unique:
                            create_table_query += f"UNIQUE({column}), "
                    foreign_key = constraints.get('foreign_key')
                    if foreign_key:
                        for column, [ref_table, ref_column] in foreign_key.items():
                            create_table_query += f"FOREIGN KEY({column}) REFERENCES {ref_table}({ref_column}), "
                    check = constraints.get('check')
                    if check:
                        for column, condition in check:
                            create_table_query += f"CHECK({column} {condition}), "
                create_table_query = create_table_query.rstrip(', ')
                create_table_query += ")"
                self.cur.execute(create_table_query)
                data = re.search(r"\((?<=\()(?:.)+", create_table_query).group()
                self.update_table(table_name, data)
                progress.next()
        self.commit()

    def commit(self) -> None:
        self.cxn.commit()

    def close(self) -> None:
        self.cxn.close()

    def run(self, command, *values) -> None:
        self.cur.execute(command, tuple(values))