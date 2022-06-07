import enum as _enum
import tkinter as _tk
import tkinter.filedialog as _fd
import tkinter.messagebox as _msg
import tkinter.ttk as _ttk

import dates
import filmview
import images
import login
import logo
import style
import util
import window
from db_sqlite import Database
from tableview import TableView
from tabs import Tabs

__all__ = ["Admin"]
_time_format = "%Y-%m-%d %H:%M"


class Admin(window.Window):
    def __init__(self):
        super().__init__("Панель администратора")
        self._db = Database()
        self._film_fields = [
            "Название",
            "Год",
            "Длительность (минуты)",
            "Описание",
            "Изображение",
        ]
        self._film_editor = None
        self._create_widgets()

    def _create_widgets(self):
        logo.get_label(self).pack()
        tabs = Tabs(self)
        tabs.populate(
            {
                self._create_films: "Фильмы и сеансы",
                self._create_stats: "Статистика",
                self._create_logins: "Кассиры",
            }
        )

    def _create_labels_entries(self, master, names):
        result = []
        for name in names:
            label = _ttk.Label(master, text=name)
            entry = style.Entry(master)
            result.append((label, entry))
        return result

    def _create_films(self, master):
        frame = _ttk.Frame(master)

        self._film_view = filmview.FilmView(frame, self._db, self._on_film_select)
        self._film_view.pack(side="left", expand=True, fill="both", padx=10, pady=10)

        add_film = self._create_add_film_frame(frame)
        add_film.pack(side="right", expand=True, fill="y")

        return frame

    def _create_add_film_frame(self, master):
        frame = _ttk.Frame(master)

        widgets = self._create_labels_entries(frame, self._film_fields)
        self._film_entries = []
        for i, pair in zip(range(len(widgets)), widgets):
            pair[0].grid(column=0, row=i, padx=5, pady=5)
            pair[1].grid(column=1, row=i, padx=5, pady=5)
            self._film_entries.append(pair[1])

        self._image_path = widgets[-1][1]
        style.Button(
            frame, text="Обзор...", command=lambda: self._select_image(self._image_path)
        ).grid(column=0, row=len(widgets) + 1, columnspan=2, padx=5, pady=5)
        style.Button(frame, text="Добавить фильм", command=self._add_film).grid(
            column=0, row=len(widgets) + 2, columnspan=2, padx=5, pady=5
        )

        return frame

    def _create_show_editor(self, _):
        self._film_editor = win = _tk.Toplevel(self)
        win.title("Редактор сеансов")
        win.grid_columnconfigure(0, weight=1)

        columns = ["ID", "film_id", "Время"]
        self._shows = TableView(
            win, self._db, "shows", columns, None, self._filter_shows
        )
        self._shows.config(displaycolumns="Время")
        self._shows.column("#1", width=180)
        self._shows.update_data()
        self._shows.grid(column=0, row=0, rowspan=6, sticky="nsew")

        _ttk.Label(win, text="Время сеанса").grid(column=1, row=0)
        self._show_time = style.Entry(win)
        self._show_time.insert(0, dates.now())
        self._show_time.grid(column=1, row=1)

        _ttk.Label(win, text="Цена билета").grid(column=1, row=2)
        self._ticket_price = style.Entry(win)
        self._ticket_price.insert(0, "100")
        self._ticket_price.grid(column=1, row=3)

        style.Button(win, text="Добавить сеанс", command=self._add_show).grid(
            column=1, row=4
        )
        style.Button(win, text="Удалить сеанс", command=self._delete_show).grid(
            column=1, row=5
        )

    def _create_film_editor(self, data):
        self._film_editor = win = _tk.Toplevel(self)
        win.title("Редактирование фильма")

        widgets = self._create_labels_entries(win, self._film_fields)
        self._edit_entries = []
        for i, pair in zip(range(len(widgets)), widgets):
            pair[0].grid(column=0, row=i, padx=5, pady=5)
            pair[1].grid(column=1, row=i, padx=5, pady=5)
            if i != len(widgets) - 1:
                pair[1].insert(0, data[i + 1])
            self._edit_entries.append(pair[1])

        style.Button(
            win, text="Обзор...", command=lambda: self._select_image(widgets[-1][1])
        ).grid(column=0, row=len(widgets) + 1, columnspan=2, padx=5, pady=5)
        style.Button(win, text="Обновить", command=self._update_film).grid(
            column=0, row=len(widgets) + 2, columnspan=2, padx=5, pady=5
        )
        style.Button(win, text="Удалить фильм", command=self._delete_film).grid(
            column=0, row=len(widgets) + 3, columnspan=2, padx=5, pady=5
        )

    def _create_logins(self, master):
        frame = _ttk.Frame(master)

        columns = ["Логин кассира", "Пароль", "Роль"]
        self._logins = TableView(
            frame,
            self._db,
            "logins",
            columns,
            self._on_cashier_select,
            self._filter_logins,
        )
        self._logins.config(displaycolumns=[columns[0]])
        self._logins.column("#1", width=180)
        self._logins.update_data()
        self._logins.grid(column=0, row=0, rowspan=4)

        _ttk.Label(frame, text="Логин").grid(column=1, row=0)
        _ttk.Label(frame, text="Пароль").grid(column=1, row=1)

        self._login = style.Entry(frame)
        self._login.grid(column=2, row=0)
        self._password = style.Entry(frame)
        self._password.grid(column=2, row=1)

        style.Button(frame, text="Добавить", command=self._add_cashier).grid(
            column=1, row=2, columnspan=2
        )
        style.Button(frame, text="Изменить пароль", command=self._change_password).grid(
            column=1, row=3, columnspan=2
        )
        return frame

    def _create_stats(self, master):
        frame = _ttk.Frame(master)
        return frame

    def _select_image(self, entry):
        filename = _fd.askopenfilename(filetypes=[("Картинки", ".jpg .png")])
        if not filename:
            return

        entry.delete(0, "end")
        entry.insert(0, filename)

    def _validate_film_data(self, entries, check_image=True):
        data = [e.get_strip() for e in entries]
        if not data[0]:
            return util.show_error("Введите название фильма")
        if (
            not data[1]
            or not data[1].isdigit()
            or int(data[1]) < 1900
            or int(data[1]) > 2022
        ):
            return util.show_error("Введите год выхода (1900-2022)")
        if not data[2] or not data[2].isdigit() or int(data[2]) < 10:
            return util.show_error("Введите длительность (от 10 мин)")
        if not data[3]:
            return util.show_error("Введите описание")
        if check_image and not data[4]:
            return util.show_error("Выберите картинку для фильма")
        if check_image and not images.is_image(data[4]):
            return util.show_error("Не удалось открыть картинку")

        return True

    def _add_film(self):
        if not self._validate_film_data(self._film_entries):
            return

        fields = [e.get_strip() for e in self._film_entries]
        if not self._db.add_film(*fields[:-1], images.create_thumbnail(fields[-1])):
            return util.show_error("Не удалось добавить фильм")

        util.show_info("Фильм добавлен")
        self._film_view.update()
        [e.delete(0, "end") for e in self._film_entries]

    def _add_show(self):
        show_time = self._show_time.get_strip()
        if not show_time or not dates.to_date(show_time):
            return util.show_error("Введите время сеанса (ГГГГ-ММ-ДД ЧЧ:ММ)")

        price = self._ticket_price.get_strip()
        if not price.isdigit() or int(price) < 0:
            return util.show_error("Введите цену билета (>0)")

        try:
            tickets = self._db.add_show(self._film_id, show_time, price)
        except:
            return util.show_error("Не удалось добавить сеанс (возможно, время занято)")

        util.show_info("Добавлен сеанс и %d билетов" % tickets)
        self._show_time.delete(0, "end")
        self._shows.update_data()

    def _delete_show(self):
        if not self._shows.selection():
            return util.show_error("Выберите сеансы для удаления")

        if not _msg.askyesno(
            "Подтверждение", "Удалить сеансов: %d?" % len(self._shows.selection())
        ):
            return

        for item in self._shows.selection():
            row = self._shows.item(item)
            self._db.delete_show(row["values"][0])

        self._shows.update_data()

    def _update_film(self):
        image_path = self._edit_entries[-1].get_strip()
        if not self._validate_film_data(self._edit_entries, bool(image_path)):
            return

        data = [e.get_strip() for e in self._edit_entries]
        if image_path:
            data[-1] = images.create_thumbnail(data[-1])
        else:
            data[-1] = None

        if self._db.update_film(self._film_id, *data):
            util.show_info("Информация обновлена")
            self._film_view.update()
        else:
            util.show_error("Не удалось обновить фильм")

    def _delete_film(self):
        if not _msg.askyesno("Подтверждение", "Вы точно хотите удалить фильм?"):
            return
        self._db.delete_film(self._film_id)
        self._film_view.update()
        self._film_editor.destroy()
        self._film_editor = None

    def _add_cashier(self):
        login_, password = self._login.get_strip(), self._password.get_strip()
        if not login_ or not password:
            return util.show_error("Введите логин и пароль")
        if self._db.get_user(login_):
            return util.show_error("Логин занят")

        self._db.register_user(
            login_, login.hash_pwd(password), login.Roles.CASHIER.value
        )
        util.show_info("Кассир %s добавлен" % login_)
        self._logins.update_data()

    def _change_password(self):
        login_, password = self._login.get_strip(), self._password.get_strip()
        if not login_ or not password:
            return util.show_error("Введите логин и пароль")
        user = self._db.get_user(login_)
        if not user:
            return util.show_error("Логин не найден")
        if user[1] == login.Roles.ADMIN.value:
            return util.show_error("Нельзя изменить пароль администратору")

        self._db.change_user_password(login_, login.hash_pwd(password))
        util.show_info("Пароль кассира %s изменён" % login_)

    def _on_film_select(self, data):
        if self._film_editor is not None:
            self._film_editor.destroy()
            self._film_editor = None

        self._film_id = data[0]
        if _msg.askyesno(
            "Выбор", "Да - добавить новый сеанс, нет - редактировать фильм"
        ):
            self._create_show_editor(data)
        else:
            self._create_film_editor(data)

    def _on_cashier_select(self, _, selected):
        self._login.delete(0, "end")
        self._login.insert(0, selected["values"][0])

    def _filter_shows(self, row):
        if int(row[1]) == self._film_id:
            return row
        return None

    def _filter_logins(self, row):
        if row[2] == "cashier":
            return row
        return None
