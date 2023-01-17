from os.path import isfile
from sqlite3 import Connection, Cursor, connect


class DB:
    DB_PATH = "./data/database.db"
    BUILD_PATH = "./data/build.sql"
    cxn: Connection
    cur: Cursor

    def __init__(self):
        self.cxn = connect(self.DB_PATH, check_same_thread=False)
        self.cur = self.cxn.cursor()

    def build(self) -> None:
        if isfile(self.BUILD_PATH):
            self.scriptexec(self.BUILD_PATH)

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
        self.commit()

    def multiexec(self, command, valueset) -> None:
        self.cur.execute(command, valueset)
        self.commit()

    def scriptexec(self, path) -> None:
        with open(path, "r", encoding='utf-8') as script:
            self.cur.executescript(script.read().__str__())
