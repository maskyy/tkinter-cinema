import functools as _ft
import io as _io
import tkinter.ttk as _ttk

import images
import style

__all__ = ["FilmView"]
_columns = 4


class FilmView(_ttk.Frame):
    def __init__(self, master=None, db=None, on_click=None):
        super().__init__(master)
        self._db = db
        self._on_click = on_click
        self.images, self.buttons = [], []

        self.update()

    def _clear_children(self):
        widgets = [w for w in self.children.values()]
        [w.destroy() for w in widgets]

    def _add_label(self):
        _ttk.Label(self, text="Фильмы не найдены...").grid(column=0, row=0)

    def update(self, filter=None):
        self._clear_children()
        self.images.clear()
        self.buttons.clear()

        films = self._db.get_table("films")
        if len(films) == 0:
            self._add_label()
            return

        row, column = 0, 0
        for film in films:
            if callable(filter) and not filter(film):
                continue

            image = images.get_photo_image(film[-1])
            btn = style.Button(
                self, image=image, command=_ft.partial(self._on_click, film)
            )
            btn.config(pad="1m")
            btn.grid(column=column, row=row)
            column += 1
            if column >= _columns:
                column = 0
                row += 1

            self.images.append(image)
            self.buttons.append(btn)

        if column == 0:  # no films were added
            self._add_label()