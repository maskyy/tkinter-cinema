import functools as _ft
import tkinter as _tk
import tkinter.messagebox as _msg
import tkinter.ttk as _ttk

import filmview
import login
import logo
import style
import util
from db_sqlite import Database
from tableview import TableView
from tabs import Tabs
from window import Window

__all__ = ["Cashier"]


class Cashier(Window):
    def __init__(self):
        super().__init__("Касса")
        self._db = Database()
        self._show_selector = self._ticket_selector = None
        self._tickets_to_sell = []
        self._update_sold_tickets()

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
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=2)
        frame.grid_rowconfigure(1, weight=1)

        self._film_view = filmview.FilmView(frame, self._db, self._on_film_select)
        self._film_view.grid(column=0, row=1)

        self._check_text = _ttk.Label(frame)
        self._check_text.grid(column=1, row=0)
        self._update_check_id()

        self._check = TableView(frame, columns=["ID", "Билет", "Стоимость"])
        self._check.config(displaycolumns=["Билет", "Стоимость"])
        self._check.column("#1", width=300)
        self._check.column("#2", width=1)
        self._check.grid(column=1, row=1, sticky="nsew", padx=20)

        check_items = _ttk.Frame(frame)
        self._create_check_items(check_items)
        check_items.grid(column=1, row=2)

        return frame

    def _create_check_items(self, master):
        self._create_confirm_window()

        self._check_sum = 0
        self._sum_label = _ttk.Label(master, text="Сумма: 0")
        self._sum_label.pack(pady=5)
        style.Button(master, text="Продать", command=self._on_sell).pack(pady=5)
        style.Button(master, text="Вернуть", command=self._on_return).pack(pady=5)

    def _create_confirm_window(self):
        self._confirm_window = _tk.Toplevel(self)
        self._confirm_window.overrideredirect(True)
        login.Login(
            self._confirm_window,
            [
                (
                    "Подтвердить",
                    lambda d, l, p: login.Login.check_credentials(
                        d, l, p, self._check_return
                    ),
                )
            ],
            self._db,
        ).pack()
        self._confirm_window.withdraw()

    def _create_returns(self, master):
        frame = _ttk.Frame(master)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=2)
        frame.grid_rowconfigure(0, weight=1)

        self._checks = TableView(frame, self._db, "checks", ["ID чека", "Сумма"])
        self._checks.grid(column=0, row=0, sticky="nsew", padx=5, pady=5)

        sales_cols = ["ID", "ID чека", "Билет", "Стоимость"]
        self._sales = TableView(frame, self._db, "sales", sales_cols)
        self._sales.config(displaycolumns=[x for x in sales_cols if x != "ID"])
        self._sales.grid(column=1, row=0, sticky="nsew", padx=5, pady=5)
        self._update_sales()

        style.Button(frame, text="Вернуть", command=self._on_return_sales).grid(
            column=0, row=1, columnspan=2, pady=5
        )

        return frame

    def _on_film_select(self, data):
        self._close_show_selector()
        self._close_ticket_selector()

        self._film_id = data[0]
        self._show_selector = win = _tk.Toplevel(self)
        win.title("Выбор сеанса")

        _ttk.Label(win, text=data[1]).pack()
        columns = ["ID", "film_id", "Время"]
        self._shows = TableView(
            win, self._db, "shows", columns, self._select_ticket, self._filter_shows
        )
        self._shows.config(displaycolumns="Время")
        self._shows.column("#1", width=180)
        self._shows.update_data()
        self._shows.pack()

        if len(self._shows.get_children()) == 0:
            util.show_error("У выбранного фильма нет сеансов")
            self._close_show_selector()

    def _close_show_selector(self):
        if self._show_selector is not None:
            self._show_selector.destroy()
            self._show_selector = None

    def _filter_shows(self, row):
        if int(row[1]) == self._film_id:
            return row
        return None

    def _select_ticket(self, _, selected):
        self._close_show_selector()
        self._close_ticket_selector()

        self._show_id = selected["values"][0]

        self._ticket_selector = win = _tk.Toplevel(self)
        self._ticket_selector.title("Выбор билета")

        _ttk.Label(win, text="Сеанс в " + selected["values"][2]).pack()
        tickets = self._create_ticket_buttons(win)
        tickets.pack()

    def _create_ticket_buttons(self, master):
        frame = _ttk.Frame(master)

        column, row = 0, 0
        for id_, price, place in self._db.get_show_tickets(self._show_id):
            btn = style.Button(frame, text="м. %d, %d р." % (place, price))
            btn.config(
                pad="1m", command=_ft.partial(self._add_ticket, id_, price, place)
            )
            btn.grid(column=column, row=row)

            if self._is_sold(id_):
                btn.config(state="disabled")

            column += 1
            if column >= 5:
                column = 0
                row += 1

        return frame

    def _filter_tickets(self, row):
        if int(row[1]) == self._show_id:
            return row
        return None

    def _close_ticket_selector(self):
        if self._ticket_selector is not None:
            self._ticket_selector.destroy()
            self._ticket_selector = None

    def _is_sold(self, id_):
        return id_ in self._tickets_to_sell or id_ in self._sold_tickets

    def _add_ticket(self, id_, price, place):
        self._close_ticket_selector()

        self._tickets_to_sell.append(id_)
        name = self._db.get_ticket_name(id_)
        self._check.insert("", "end", values=(id_, name, price))
        self._update_check_sum()

    def _on_sell(self):
        if len(self._check.get_children()) == 0:
            return util.show_error("В чеке нет товаров")

        self._db.add_check(self._check_id, self._check_sum)
        for row in self._check.get_children():
            values = self._check.item(row)["values"]
            self._db.sell_ticket(self._check_id, values[0], values[2])

        self._tickets_to_sell.clear()
        self._update_sold_tickets()
        self._check.clear()
        self._db.save()

        util.show_info("Чек №%d на сумму %d" % (self._check_id, self._check_sum))
        self._update_check_id()
        self._update_check_sum()
        self._update_sales()

    def _check_return(self, role):
        if role != login.Roles.ADMIN.value:
            return util.show_error("Введите логин и пароль администратора")
        self._do_return()
        self._confirm_window.withdraw()

    def _on_return(self):
        if self._confirm_window.winfo_ismapped():
            self._confirm_window.withdraw()
            return
        if not self._check.selection():
            return util.show_error("Выберите билеты для возврата")
        self._confirm_window.deiconify()
        util.center_window(self._confirm_window)

    def _do_return(self):
        if not self._check.selection():
            return util.show_error("Выберите билеты для возврата")

        for row in self._check.selection():
            values = self._check.item(row)["values"]
            self._tickets_to_sell.remove(values[0])
            self._check.delete(row)

        self._update_check_sum()

    def _on_return_sales(self):
        if not self._checks.selection() and not self._sales.selection():
            return util.show_error("Выберите хотя бы один чек или билет для возврата")
        selected_sales = list(self._sales.selection())

        for check in self._checks.selection():
            check_id = self._checks.item(check)["values"][0]
            selected_sales += self._find_sales(check_id)
        selected_sales = set(selected_sales)

        if not _msg.askyesno(
            "Подтверждение",
            "Вернуть чеков: %d, товаров: %d?"
            % (len(self._checks.selection()), len(selected_sales)),
        ):
            return

        for sale in selected_sales:
            # ID записи в первом столбце (скрытом)
            values = self._sales.item(sale)["values"]
            self._db.return_sale(values[0])

        for check in self._checks.selection():
            values = self._checks.item(check)["values"]
            self._db.return_check(values[0])

        self._update_sales()
        self._update_check_id()
        self._update_sold_tickets()

    def _find_sales(self, check_id):
        result = []
        for row in self._sales.get_children():
            values = self._sales.item(row)["values"]
            if values[1] == check_id:
                result.append(row)
        return result

    def _update_check_id(self):
        self._check_id = self._db.get_new_check_id()
        self._check_text.config(text="Чек №%d" % self._check_id)

    def _update_check_sum(self):
        result = 0
        for row in self._check.get_children():
            result += self._check.item(row)["values"][2]
        self._check_sum = result
        self._sum_label.config(text="Сумма: %d" % self._check_sum)

    def _update_sold_tickets(self):
        self._sold_tickets = self._db.get_sold_tickets()
        self._sold_tickets = [item[0] for item in self._sold_tickets]

    def _update_sales(self):
        self._checks.update_data()
        self._sales.update_data()