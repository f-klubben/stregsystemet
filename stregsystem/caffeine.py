from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List


CAFFEINE_IN_COFFEE = 70
CAFFEINE_DEGRADATION_PR_HOUR = 0.12945
CAFFEINE_TIME_INTERVAL = timedelta(days=1)


@dataclass
class Intake:
    mg: int
    time: datetime


def caffeine_mg_to_coffee_cups(mg: int) -> int:
    return int(mg / CAFFEINE_IN_COFFEE)


def calc_caffeine_str(caffeine):
    coffee_str = ""
    for coffee_cup in range(0, int(caffeine / CAFFEINE_IN_COFFEE)):
        coffee_str += "&#9749;"  # HTML-code for ☕
    return coffee_str


def current_caffeine_mg_level(now, intakes: List[Intake]):
    from dateutil.rrule import rrule, HOURLY

    previous_day = now - CAFFEINE_TIME_INTERVAL

    in_blood = 0
    hour: datetime
    for hour in rrule(HOURLY, dtstart=previous_day, until=now):
        in_blood -= in_blood * CAFFEINE_DEGRADATION_PR_HOUR

        intake_this_hour = filter(lambda i: i.time.hour == hour.hour, intakes)
        sum_this_hour = sum(i.mg for i in intake_this_hour)
        in_blood += sum_this_hour

    return in_blood
