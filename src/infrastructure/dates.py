from datetime import date, datetime, timedelta


def get_first_date_of_current_month() -> date:
    """base on the current date information get the first date
    of the current month and convert it to the `date` instance.
    """

    return datetime.strptime(
        f"{date.today().strftime("%Y-%m")}-01", "%Y-%m-%d"
    ).date()


def get_previous_month_range() -> tuple[date, date]:
    """base on the current date information get the first and the last dates
    of the previous month and convert them to the `date` instances.
    """

    today: date = date.today()

    last_day: date = datetime.strptime(
        f"{today.strftime("%Y-%m")}-01", "%Y-%m-%d"
    ).date() - timedelta(days=1)

    first_day: date = datetime.strptime(
        f"{last_day.strftime("%Y-%m")}-01", "%Y-%m-%d"
    ).date()

    return first_day, last_day
