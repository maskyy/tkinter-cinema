import enum as _enum
import tkinter as _tk
import tkinter.filedialog as _fd
import tkinter.messagebox as _msg
import tkinter.ttk as _ttk

import filmview
import images
import logo
import style
import util
import window

from db_sqlite import Database
from tableview import TableView
from tabs import Tabs

__all__ = ["Admin"]


class Admin(window.Window):
    def __init__(self):
        super().__init__("Панель администратора")
        self._db = Database()
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
        frame.grid_columnconfigure(0, weight=2)
        frame.grid_columnconfigure(1, weight=1)

        self._film_view = filmview.FilmView(frame, self._db, self._on_film_select)
        self._film_view.grid(column=0, row=0)

        add_film = self._create_add_film_frame(frame)
        add_film.grid(column=1, row=0)

        return frame

    def _create_add_film_frame(self, master):
        frame = _ttk.Frame(master)

        fields = ["Название", "Год", "Длительность (минуты)", "Описание", "Изображение"]
        widgets = self._create_labels_entries(frame, fields)
        self._add_entries = []
        for i, pair in zip(range(len(widgets)), widgets):
            pair[0].grid(column=0, row=i, padx=5, pady=5)
            pair[1].grid(column=1, row=i, padx=5, pady=5)
            self._add_entries.append(pair[1])

        self._image_path = widgets[-1][1]
        style.Button(frame, text="Обзор...", command=self._select_image).grid(
            column=0, row=len(widgets) + 1, columnspan=2, padx=5, pady=5
        )
        style.Button(frame, text="Добавить фильм", command=self._add_film).grid(
            column=0, row=len(widgets) + 2, columnspan=2, padx=5, pady=5
        )

        return frame

    def _create_logins(self, master):
        frame = _ttk.Frame(master)
        return frame

    def _create_stats(self, master):
        frame = _ttk.Frame(master)
        return frame

    def _select_image(self):
        filename = _fd.askopenfilename(filetypes=[("Картинки", ".jpg .png")])
        if not filename:
            return

        self._image_path.delete(0, "end")
        self._image_path.insert(0, filename)

    def _validate_film_data(self):
        data = [e.get_strip() for e in self._add_entries]
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
        if not data[4]:
            return util.show_error("Выберите картинку для фильма")
        if not images.is_image(data[4]):
            return util.show_error("Не удалось открыть картинку")

        return True

    def _add_film(self):
        if not self._validate_film_data():
            return

        fields = [e.get_strip() for e in self._add_entries]
        if not self._db.add_film(*fields[:-1], images.create_thumbnail(fields[-1])):
            return util.show_error("Не удалось добавить фильм")

        util.show_info("Фильм добавлен")
        self._film_view.update()
        [e.delete(0, "end") for e in self._add_entries]

    def _on_film_select(self, id_):
        _msg.askyesno("aa", id_)
