import tkinter as _tk
import tkinter.ttk as _ttk

import logo
import util
from db_sqlite import Database
from login import Login, Roles
from style import Button, Entry
from tableview import TableView
from tabs import Tabs
from window import Window

__all__ = ["Cashier"]


class Cashier(Window):
    def __init__(self):
        super().__init__("Касса")
        self._db = Database()
        self._create_widgets()

    def _create_widgets(self):
        logo.get_label(self).pack()
        tabs = Tabs(self)
        tabs.populate(
            {
                self._create_main: "Продажа",
                self._create_returns: "Возврат",
            }
        )

    def _create_main(self, master):
        frame = _ttk.Frame(master)
        frame.grid_columnconfigure(0, weight=2)
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        _ttk.Label(frame, text="Билеты").grid(column=0, row=0)
        self._check_text = _ttk.Label(frame)
        self._check_text.grid(column=1, row=0)
        self._update_check_id()

        cols = ["ID", "ID сеанса", "Количество", "Цена"]
        self._tickets = TableView(
            frame, self._db, "tickets", cols, self._on_ticket_select
        )
        self._tickets.grid(column=0, row=1, sticky="nsew", padx=20)
        self._tickets.update_data()

        entries = _ttk.Frame(frame)
        self._create_entries(entries)
        entries.grid(column=0, row=2)

        self.check = TableView(frame, columns=["Штрихкод", "Количество", "Стоимость"])
        self.check.grid(column=1, row=1, sticky="nsew", padx=20)

        check_items = _ttk.Frame(frame)
        self._create_check_items(check_items)
        check_items.grid(column=1, row=2)

        return frame

    def _create_entries(self, master):
        _ttk.Label(master, text="ID").grid(column=0, row=0, padx=5)
        _ttk.Label(master, text="Количество").grid(column=0, row=1, padx=5)

        self._code = Entry(master)
        self._code.grid(column=1, row=0, padx=5, pady=5)
        self._amount = Entry(master)
        self._amount.grid(column=1, row=1, padx=5, pady=5)

        add = Button(master, text="Добавить", command=self.on_add_item)
        add.grid(column=0, row=2, columnspan=2, pady=5)

        self._code.bind("<Return>", lambda _: add.invoke())
        self._amount.bind("<Return>", lambda _: add.invoke())

    def _create_check_items(self, master):
        self._create_confirm_window()

        self._check_sum = 0
        self._sum_label = _ttk.Label(master, text="Сумма: 0")
        self._sum_label.pack(pady=5)
        Button(master, text="Продать", command=self.on_sell).pack(pady=5)
        Button(master, text="Вернуть", command=self.on_return).pack(pady=5)

    def _create_confirm_window(self):
        self._confirm_window = _tk.Toplevel(self)
        self._confirm_window.overrideredirect(True)
        Login(
            self._confirm_window,
            [
                (
                    "Подтвердить",
                    lambda l, p: Login.check_credentials(l, p, self.check_return),
                )
            ],
        ).pack()
        self._confirm_window.withdraw()

    def _create_returns(self, master):
        frame = _ttk.Frame(master)
        return frame

    def _find_row(self, table, code):
        for row in table.get_children():
            if int(code) == table.item(row)["values"][0]:
                return row, table.item(row)["values"]
        return None, None

    def _on_ticket_select(self, _, selected):
        return
        self.code.delete(0, "end")
        self.amount.delete(0, "end")
        self.code.insert(0, selected["values"][0])
        self.amount.insert(0, 1)
        self.code.focus()

    def on_add_item(self):
        code, amount = self.code.get_strip(), self.amount.get_strip()
        if not code or len(code) != 13 or not code.isdigit():
            return util.show_error("Введите штрихкод из 13 цифр")

        row, values = self.find_row(self.goods, code)

        if not row:
            return util.show_error("Штрихкод не найден")
        if not amount.isdigit() or int(amount) <= 0:
            return util.show_error("Количество должно быть целым положительным числом")
        amount = int(amount)
        if amount > values[3]:
            return util.show_error("Нельзя продать больше товаров, чем есть в наличии")

        self.change_by_amount(-amount, row)
        self.add_to_check(code, amount, row)
        self.update_check_sum()

        self.code.delete(0, "end")
        self.amount.delete(0, "end")

    def change_by_amount(self, amount, row):
        values = self.goods.item(row)["values"]
        values[3] += amount
        self.goods.item(row, values=values)

    def add_to_check(self, code, amount, row):
        cost = amount * self.goods.item(row)["values"][4]
        self.check.insert("", "end", values=(code, amount, cost))

    def on_sell(self):
        if len(self.check.get_children()) == 0:
            return util.show_error("В чеке нет товаров")

        self.db.add_check(self.check_id, self.check_sum)
        for row in self.check.get_children():
            data = (self.check_id, *self.check.item(row)["values"])
            self.db.sell_product(*data)

        self.check.clear()
        self.db.save()

        util.show_info("Чек №%d на сумму %d" % (self.check_id, self.check_sum))
        self.update_check_id()
        self.update_check_sum()

    def check_return(self, role):
        if role != Roles.ADMIN:
            return util.show_error("Введите логин и пароль администратора")
        self.do_return()
        self.confirm_window.withdraw()

    def on_return(self):
        if self.confirm_window.winfo_ismapped():
            self.confirm_window.withdraw()
            return
        if not self.check.selection():
            return util.show_error("Выберите товары для возврата")
        self.confirm_window.deiconify()
        util.center_window(self.confirm_window)

    def do_return(self):
        if not self.check.selection():
            return util.show_error("Выберите товары для возврата")

        for row in self.check.selection():
            values = self.check.item(row)["values"]
            goods_row, _ = self.find_row(self.goods, values[0])
            self.change_by_amount(values[1], goods_row)
            self.check.delete(row)

        self.update_check_sum()

    def _update_check_id(self):
        self._check_id = self._db.get_new_check_id()
        self._check_text.config(text="Чек №%d" % self._check_id)

    def update_check_sum(self):
        result = 0
        for row in self.check.get_children():
            result += self.check.item(row)["values"][2]
        self.check_sum = result
        self.sum_label.config(text="Сумма: %d" % self.check_sum)
