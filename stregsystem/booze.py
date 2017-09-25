from enum import Enum
import datetime


def _alcohol_ml_to_gram(ml):
    return ml * 0.789


def _alcohol_gram_to_ml(gram):
    return gram / 0.789


class Gender(Enum):
    MALE = 1
    FEMALE = 2
    UNKNOWN = 3


def _percent_water(gender):
    if gender == Gender.MALE:
        return .7
    elif gender == Gender.FEMALE:
        return .6
    elif gender == Gender.UNKNOWN:
        return .65


def _water_weight(gender, weight):
    return _percent_water(gender) * weight


def alcohol_bac_increase(gender, weight, alcohol_ml):
    return (
        _alcohol_ml_to_gram(alcohol_ml)
        / _water_weight(gender, weight))


def alcohol_bac_degredation(time):
    time_hours = time.total_seconds()/3600
    return 0.15 * time_hours


def alcohol_bac_timeline(gender, weight, now, alcohol_timeline):
    # If we didn't drink anything, we can't have any alcohol
    if len(alcohol_timeline) == 0:
        return 0

    # We assume a start BAC of 0
    current = 0
    # None means this is first iteration
    last_time = None
    for time, ml in alcohol_timeline:

        # First iteration has BAC 0, and a BAC of 0 can't degrade, so the first
        # iteration doesn't need degredation
        if last_time is not None:
            time_diff = time - last_time
            current -= alcohol_bac_degredation(time_diff)

        last_time = time

        # A negative BAC doesn't make sense
        if current < 0:
            current = 0

        current += alcohol_bac_increase(gender, weight, ml)

        # last_time can never be None after the first iteration
        assert(last_time is not None)

    # Since we return if the list is empty we must have some last time
    assert(last_time is not None)

    # We also need to remove the degredation from the last drink till now
    time_diff = now - last_time
    current -= alcohol_bac_degredation(time_diff)

    if current < 0:
        current = 0

    return current
