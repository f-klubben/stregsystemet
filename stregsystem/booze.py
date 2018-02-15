from enum import Enum

BAC_DEGRADATION_PR_HOUR = 0.15


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


def alcohol_bac_degradation(time):
    time_hours = time.total_seconds() / 3600
    return BAC_DEGRADATION_PR_HOUR * time_hours


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
            current -= alcohol_bac_degradation(time_diff)

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
    current -= alcohol_bac_degradation(time_diff)

    if current < 0:
        current = 0

    return current


# Ballmer peak: 1.337 +/- 0.05
BALLMER_PEAK_MEAN = 1.337
BALLMER_PEAK_LOWER_LIMIT = BALLMER_PEAK_MEAN - 0.05
BALLMER_PEAK_UPPER_LIMIT = BALLMER_PEAK_MEAN + 0.05


def ballmer_peak(bac):
    def bac_delta_to_time(bac_delta):
        return divmod(bac_delta / BAC_DEGRADATION_PR_HOUR * 3600, 60)

    if BALLMER_PEAK_LOWER_LIMIT < bac < BALLMER_PEAK_UPPER_LIMIT:
        # First get the distance in bac till we leave the Ballmer peak
        difference_to_exit = bac - BALLMER_PEAK_LOWER_LIMIT

        # We leave Ballmer peak once we drop below the lower limit. To find the distance in time.
        # We do the reverse of the alcohol_bac_degradation, i.e. given a BAC delta, get the timedelta.
        minutes, seconds = bac_delta_to_time(difference_to_exit)
        return True, int(minutes), int(seconds)
    elif bac > BALLMER_PEAK_UPPER_LIMIT:
        # We're above the limit, find the bac delta until  we reach Ballmer peak
        difference_to_enter = bac - BALLMER_PEAK_UPPER_LIMIT
        minutes, seconds = bac_delta_to_time(difference_to_enter)
        return False, int(minutes), int(seconds)
    else:
        return False, None, None
