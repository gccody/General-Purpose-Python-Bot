import re
import sys
from sqlite3 import Connection, Cursor, connect, Error


class DB:
    DB_PATH = "./data/database.db"
    cxn: Connection
    cur: Cursor

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

    def __init__(self):
        self.cxn = connect(self.DB_PATH, check_same_thread=False)
        self.cur = self.cxn.cursor()

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
        print('Building Database...')
        for table in self.table_info:
            table_data = table['table']
            for table_name, columns in table_data.items():
                print(f' - {table_name}')
                create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name}("
                constraints = table.get('constraints')
                for column_name, data_type in columns.items():
                    print(f'    - {column_name}')
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
        self.commit()

    def commit(self) -> None:
        self.cxn.commit()

    def close(self) -> None:
        self.cxn.close()

    def field(self, command, *values):
        self.cur.execute(command, tuple(values))

        if (fetch := self.cur.fetchone()) is not None:
            return fetch[0]

    def record(self, command, *values):
        self.cur.execute(command, tuple(values))

        return self.cur.fetchone()

    def records(self, command, *values) -> list:
        self.cur.execute(command, tuple(values))

        return self.cur.fetchall()

    def execute(self, command, *values) -> None:
        self.cur.execute(command, tuple(values))

    def multiexec(self, command, valueset) -> None:
        self.cur.execute(command, valueset)
