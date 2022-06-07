import sqlite3 as _sql

__all__ = ["Database"]

_default_name = "files/cinema.sqlite3"
_cinema_places = 20

_init_script = (
    """
PRAGMA encoding = "UTF-8";
PRAGMA foreign_keys = 1;

PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;

CREATE TABLE IF NOT EXISTS films (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    year INTEGER NOT NULL,
    duration_min INTEGER NOT NULL CHECK(duration_min >= 0),
    description TEXT NOT NULL,
    image BLOB NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS shows (
    id INTEGER PRIMARY KEY,
    film_id INTEGER NOT NULL,
    time TEXT NOT NULL UNIQUE,
    FOREIGN KEY(film_id) REFERENCES films(id) ON DELETE CASCADE
) STRICT;

CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY,
    show_id INTEGER NOT NULL,
    price INTEGER NOT NULL DEFAULT 0 CHECK(price >= 0),
    place INTEGER NOT NULL CHECK(place >= 0 AND place < %d),
    FOREIGN KEY(show_id) REFERENCES shows(id) ON DELETE CASCADE
) STRICT;

CREATE TABLE IF NOT EXISTS checks (
    id INTEGER PRIMARY KEY,
    sum INTEGER NOT NULL DEFAULT 0 CHECK(sum >= 0)
) STRICT;

CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY,
    check_id INTEGER NOT NULL,
    ticket_id INTEGER NOT NULL UNIQUE,
    cost INTEGER NOT NULL DEFAULT 0 CHECK(cost >= 0),
    FOREIGN KEY(check_id) REFERENCES checks(id) ON DELETE CASCADE,
    FOREIGN KEY(ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
) STRICT;

CREATE TABLE IF NOT EXISTS logins (
    login TEXT PRIMARY KEY,
    password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT "cashier"
) STRICT;

CREATE VIEW IF NOT EXISTS stats AS
SELECT films.id as id, films.name as name, COUNT(ticket_id) as tickets, SUM(cost) as profit
FROM sales
INNER JOIN tickets ON sales.ticket_id = tickets.id
INNER JOIN shows ON tickets.show_id = shows.id
INNER JOIN films ON shows.film_id = films.id
GROUP BY films.id
ORDER BY profit DESC;
"""
    % _cinema_places
)

_exit_script = """
PRAGMA analysis_limit = 1000;
PRAGMA optimize;
"""


class Database:
    def __init__(self, filename=_default_name):
        self._con = _sql.connect(filename)
        self._cur = self._con.cursor()
        self._cur.executescript(_init_script)

    def __del__(self):
        self._cur.executescript(_exit_script)
        self._cur.close()
        self.save()
        self._con.close()

    def save(self):
        self._con.commit()

    def get_table(self, name):
        return self._cur.execute("SELECT * FROM %s" % name).fetchall()

    def execute(self, *args):
        return self._cur.execute(*args)

    def get_columns(self, table):
        self._cur.execute("SELECT name FROM PRAGMA_TABLE_INFO('%s')" % table)
        return [name[0] for name in self._cur.fetchall()]

    def get_user(self, login):
        self._cur.execute("SELECT password, role FROM logins WHERE login = ?", (login,))
        result = self._cur.fetchone()
        return result

    def register_user(self, login, password, role):
        self._cur.execute(
            "INSERT INTO logins VALUES (?, ?, ?)", (login, password, role)
        )
        self.save()

    def change_user_password(self, login, new_password):
        self._cur.execute(
            "UPDATE logins SET password = ? WHERE login = ?", (new_password, login)
        )
        self.save()

    def get_new_check_id(self):
        result = self._cur.execute("SELECT MAX(id)+1 FROM checks").fetchone()[0]
        return 1 if not result else result

    def get_show_tickets(self, show_id):
        self._cur.execute(
            "SELECT id, price, place FROM tickets WHERE show_id = ?", (show_id,)
        )
        return self._cur.fetchall()

    def get_sold_tickets(self):
        self._cur.execute("SELECT ticket_id FROM sales")
        return self._cur.fetchall()

    def sell_ticket(self, check_id, ticket_id, cost):
        self._cur.execute(
            "INSERT INTO sales VALUES (NULL, ?, ?, ?)", (check_id, ticket_id, cost)
        )

    def add_check(self, id_, sum_):
        self._cur.execute("INSERT INTO checks VALUES (?, ?)", (id_, sum_))

    def return_check(self, id_):
        self._cur.execute("DELETE FROM checks WHERE id = ?", (id_,))

    def get_ticket_name(self, ticket_id):
        self._cur.execute(
            "SELECT show_id, place FROM tickets WHERE id = ?", (ticket_id,)
        )
        show_id, place = self._cur.fetchone()
        self._cur.execute("SELECT film_id, time FROM shows WHERE id = ?", (show_id,))
        film_id, time = self._cur.fetchone()
        self._cur.execute("SELECT name FROM films WHERE id = ?", (film_id,))
        (name,) = self._cur.fetchone()
        return "%s (%s, м. %d)" % (name, time, place)

    def sell_ticket(self, check_id, ticket_id, cost):
        self._cur.execute(
            "INSERT INTO sales VALUES (NULL, ?, ?, ?)", (check_id, ticket_id, cost)
        )

    def return_sale(self, id_):
        self._cur.execute("SELECT check_id, cost FROM sales WHERE id = ?", (id_,))
        check_id, cost = self._cur.fetchone()
        self._cur.execute("DELETE FROM sales WHERE id = ?", (id_,))
        self._cur.execute(
            "UPDATE checks SET sum = sum - ? WHERE id = ?", (cost, check_id)
        )

    def add_film(self, name, year, minutes, description, image_data):
        try:
            self._cur.execute(
                "INSERT INTO films VALUES (NULL, ?, ?, ?, ?, ?)",
                (name, year, minutes, description, image_data),
            )
            return True
        except:
            return False

    def update_film(self, id_, name, year, minutes, description, image_data=None):
        args = (name, year, minutes, description)
        update_str = "name = ?, year = ?, duration_min = ?, description = ?"
        if image_data is not None:
            args += (image_data,)
            update_str += ", image = ?"

        try:
            self._cur.execute(
                "UPDATE films SET %s WHERE id = ?" % update_str, args + (id_,)
            )
            self.save()
            return True
        except Exception as e:
            print(e)
            return False

    def delete_film(self, id_):
        self._cur.execute("DELETE FROM films WHERE id = ?", (id_,))

    def add_show(self, film_id, time, price):
        self._cur.execute("INSERT INTO shows VALUES (NULL, ?, ?)", (film_id, time))
        show_id = self._cur.execute("SELECT last_insert_rowid()").fetchone()[0]
        for i in range(_cinema_places):
            self.add_ticket(show_id, price, i)
        return _cinema_places

    def add_ticket(self, show_id, price, place):
        self._cur.execute(
            "INSERT INTO tickets VALUES (NULL, ?, ?, ?)", (show_id, price, place)
        )

    def delete_show(self, id_):
        self._cur.execute("DELETE FROM shows WHERE id = ?", (id_,))

    def get_film_shows(self, id_, time):
        time = "%%%s%%" % time
        self._cur.execute(
            "SELECT * FROM shows WHERE film_id = ? AND time LIKE ?", (id_, time)
        )
        return self._cur.fetchall()


"""
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

    def add_check(self, id_, sum_):
        self._cur.execute("INSERT INTO checks VALUES (?, ?)", (id_, sum_))

    def sell_product(self, check_id, barcode, amount, cost):
        self.change_by_amount(barcode, -amount)

        self._cur.execute(
            "INSERT INTO sales VALUES (NULL, ?, ?, ?, ?)",
            (check_id, barcode, amount, cost),
        )

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
"""
