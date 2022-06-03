import enum as _enum
import tkinter as _tk
import tkinter.messagebox as _msg
import tkinter.ttk as _ttk

import logo
import util
from db_sqlite import Database
from hint import Hint
from style import Button, Entry
from tableview import TableView
from tabs import Tabs
from window import Window

__all__ = ["Admin"]


class DeliveryActions(_enum.Enum):
    INSERT = "Вставить"
    ADD = "Добавить"
    UPDATE = "Обновить"


class Admin(Window):
    def __init__(self):
        super().__init__("Панель администратора")
        self._db = Database()
        self._goods_cols = [
            "Штрихкод",
            "Наименование",
            "Производитель",
            "Количество",
            "Цена",
        ]

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

    def _create_films(self, master):
        frame = _ttk.Frame(master)

        return frame

    def _create_logins(self, master):
        frame = _ttk.Frame(master)
        return frame

    def _create_stats(self, master):
        frame = _ttk.Frame(master)
        return frame
