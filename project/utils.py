from datetime import datetime, timedelta, timezone
from dateutil import relativedelta
import pytz

def get_midnight(date):
    return (date.replace(hour=0, minute=0, second=0, microsecond=0))

def get_end_of_a_month(date, month_interval):
    return (get_midnight(date) + relativedelta.relativedelta(day=1, months=month_interval, days=-1))

def convert_to_utc(date):
    date = datetime.strptime(date,'%Y-%m-%d %H:%M:%S%z')
    date = date.astimezone(pytz.utc)
    return date.replace(tzinfo=None)