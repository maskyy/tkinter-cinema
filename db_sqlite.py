import sqlite3 as _sql

__all__ = ["Database"]

_default_name = "files/cinema.sqlite3"

_init_script = """
PRAGMA encoding = 'UTF-8';
PRAGMA foreign_keys = 1;

PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;

CREATE TABLE IF NOT EXISTS films (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    year INTEGER NOT NULL,
    duration_min INTEGER NOT NULL CHECK(duration_min >= 0),
    description TEXT NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS shows (
    id INTEGER PRIMARY KEY,
    film_id INTEGER NOT NULL,
    time TEXT NOT NULL,
    FOREIGN KEY(film_id) REFERENCES films(id) ON DELETE CASCADE
) STRICT;

CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY,
    show_id INTEGER NOT NULL,
    amount INTEGER NOT NULL DEFAULT 0 CHECK(amount >= 0),
    price INTEGER NOT NULL DEFAULT 0 CHECK(price >= 0),
    FOREIGN KEY(show_id) REFERENCES shows(id) ON DELETE CASCADE
) STRICT;

CREATE TABLE IF NOT EXISTS checks (
    id INTEGER PRIMARY KEY,
    sum INTEGER NOT NULL DEFAULT 0 CHECK(sum >= 0)
) STRICT;

CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY,
    check_id INTEGER NOT NULL,
    ticket_id INTEGER NOT NULL,
    amount INTEGER NOT NULL DEFAULT 0 CHECK(amount > 0),
    cost INTEGER NOT NULL DEFAULT 0 CHECK(cost >= 0),
    FOREIGN KEY(check_id) REFERENCES checks(id) ON DELETE CASCADE,
    FOREIGN KEY(ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
) STRICT;

CREATE TABLE IF NOT EXISTS logins (
    login TEXT PRIMARY KEY,
    password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT "cashier"
) STRICT;
"""

_exit_script = """
PRAGMA analysis_limit = 1000;
PRAGMA optimize;
"""


def _check_args(length, *args):
    if length != len(*args):
        raise Exception("Wrong number of arguments")


class Database:
    def __init__(self, filename=_default_name):
        self.con = _sql.connect(filename)
        self._cur = self.con.cursor()
        self._cur.executescript(_init_script)

    def __del__(self):
        self._cur.executescript(_exit_script)
        self._cur.close()
        self.save()
        self.con.close()

    def save(self):
        self.con.commit()

    def get_table(self, name):
        return self._cur.execute("SELECT * FROM %s" % name).fetchall()

    def execute(self, *args):
        return self._cur.execute(*args)

    def get_user(self, login):
        self._cur.execute("SELECT password, role FROM logins WHERE login = ?", (login,))
        result = self._cur.fetchone()
        return result

    def register_user(self, login, password, role):
        self._cur.execute(
            "INSERT INTO logins VALUES (?, ?, ?)", (login, password, role)
        )

    def get_columns(self, table):
        self._cur.execute("SELECT name FROM PRAGMA_TABLE_INFO('%s')" % table)
        return [name[0] for name in self._cur.fetchall()]

    def add_product(self, *args):
        _check_args(5, args)
        self._cur.execute("INSERT INTO goods VALUES (?, ?, ?, ?, ?)", args)

    def update_product(self, barcode, **kwargs):
        set_str = ""
        data = []
        for key in ["name", "manufacturer", "amount", "price"]:
            if key in kwargs:
                data.append(kwargs[key])
                set_str += key + " = ?, "
        data.append(barcode)
        data = tuple(data)
        set_str = set_str[:-2]
        self._cur.execute("UPDATE goods SET %s WHERE barcode = ?" % set_str, data)

    def change_by_amount(self, barcode, amount):
        self._cur.execute("SELECT amount FROM goods WHERE barcode = ?", (barcode,))
        current = self._cur.fetchone()
        if not current:
            print("Item not found!")
            return False
        current = current[0]
        new = current + amount
        self._cur.execute(
            "UPDATE goods SET amount = ? WHERE barcode = ?", (new, barcode)
        )

    def get_new_check_id(self):
        result = self._cur.execute("SELECT MAX(id)+1 FROM checks").fetchone()[0]
        return 1 if not result else result

    def add_check(self, id_, sum_):
        self._cur.execute("INSERT INTO checks VALUES (?, ?)", (id_, sum_))

    def sell_product(self, check_id, barcode, amount, cost):
        """
        count = self._cur.execute(
            "SELECT amount FROM goods WHERE barcode = ?", (barcode,)
        ).fetchone()[0]
        new_amount = count - amount
        self._cur.execute(
            "UPDATE goods SET amount = ? WHERE barcode = ?", (new_amount, barcode)
        )
        """
        self.change_by_amount(barcode, -amount)

        self._cur.execute(
            "INSERT INTO sales VALUES (NULL, ?, ?, ?, ?)",
            (check_id, barcode, amount, cost),
        )
        """
        self._cur.execute(
            "UPDATE checks SET sum = sum + ? WHERE id = ?", (cost, check_id)
        )
        """

    def return_check(self, check_id):
        self._cur.execute("DELETE FROM checks WHERE id = ?", (check_id,))
        self._cur.execute("DELETE FROM sales WHERE check_id = ?", (check_id,))

    def return_sale(self, id_):
        self._cur.execute("SELECT check_id FROM sales WHERE id = ?", (id_,))
        check_id = self._cur.fetchone()
        if not check_id:
            print("Check not found!")
            return False
        check_id = check_id[0]
        self._cur.execute("SELECT barcode, amount, cost FROM sales WHERE id = ?", (id_,))
        barcode, amount, cost = self._cur.fetchone()

        self.change_by_amount(barcode, amount)
        self._cur.execute(
            "UPDATE checks SET sum = sum - ? WHERE id = ?", (cost, check_id)
        )
        self._cur.execute("DELETE FROM sales WHERE id = ?", (id_,))

    def reset_sales(self):
        self._cur.executescript("DELETE FROM sales; DELETE FROM checks;")