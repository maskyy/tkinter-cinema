import datetime as _dt

_date_format = "%Y-%m-%d %H:%M"


def to_date(s):
    try:
        return _dt.datetime.strptime(s, _date_format).date()
    except ValueError:
        return None


def from_date(date):
    return date.strftime(_date_format)


def now():
    return _dt.datetime.now().strftime(_date_format)
