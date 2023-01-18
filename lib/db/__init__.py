from os.path import isfile
from sqlite3 import Connection, Cursor, connect


class DB:
    DB_PATH = "./data/database.db"
    cxn: Connection
    cur: Cursor

    tables: dict[str, dict[str, str]] = {
        'bans': {
            'guild_id': 'TEXT',
            'user_id': 'TEXT',
            'mod_id': 'TEXT',
            'reason': 'TEXT',
            'ts': 'INTEGER'
        },
        'guilds': {
            'id': 'TEXT PRIMARY KEY NOT NULL',
            'level_id': 'TEXT',
            'announce_id': 'TEXT'
        },
        'reports': {
            'guild_id': 'TEXT',
            'user_id': 'TEXT',
            'target_id': 'TEXT',
            'report': 'TEXT'
        },
        'commands': {
            'command_name': 'TEXT',
            'guild_id': 'TEXT',
            'user_id': 'TEXT',
            'params': 'JSON',
            'ts': 'INTEGER'
        },
        'levels': {
            'guild_id': 'TEXT',
            'user_id': 'TEXT',
            'xp': 'INTEGER'
        },
        'youtube': {
            'handle': 'TEXT',
            'guild_id': 'TEXT',
            'message': 'TEXT',
            'latest_url': 'TEXT'
        }
    }

    def __init__(self):
        self.cxn = connect(self.DB_PATH, check_same_thread=False)
        self.cur = self.cxn.cursor()

    def update_table(self, table: str, columns_str_list: list[str], columns_list: dict[str, str]):
        self.cur.execute(f"CREATE TABLE {table}_new ({' '.join(columns_str_list)});")
        self.cur.execute(f"INSERT INTO {table}_new SELECT * FROM {table};")
        self.cur.execute(f"DROP TABLE {table};")
        self.cur.execute(f"ALTER TABLE {table}_new RENAME TO {table};")

    def build(self) -> None:
        for table, columns in self.tables.items():
            # Create tables
            columns_str_list = []
            for index, (name, data_type) in enumerate(columns.items()):
                columns_str_list.append(f"{name} {data_type}," if index < len(columns) - 1 else f"{name} {data_type}")

            self.cur.execute(f"CREATE TABLE IF NOT EXISTS {table} ({' '.join(columns_str_list)});")

            # Update tables in case the types need to be updated
            self.update_table(table, columns_str_list, columns)
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

    def column(self, command, *values) -> list:
        self.cur.execute(command, tuple(values))

        return [item[0] for item in self.cur.fetchall()]

    def execute(self, command, *values) -> None:
        self.cur.execute(command, tuple(values))

    def multiexec(self, command, valueset) -> None:
        self.cur.execute(command, valueset)
