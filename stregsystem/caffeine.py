from datetime import datetime, timedelta
from typing import List

from django.utils import timezone

CAFFEINE_IN_COFFEE = 70
CAFFEINE_DEGRADATION_PR_HOUR = 0.12945
CAFFEINE_TIME_INTERVAL = timedelta(days=1)


class Intake:
    timestamp: datetime
    mg: int

    def __init__(self, timestamp: datetime, mg: int):
        self.timestamp = timestamp
        self.mg = mg


def caffeine_mg_to_coffee_cups(mg: int) -> int:
    return int(mg / CAFFEINE_IN_COFFEE)


# calculate current caffeine in body, takes list of intakes, applies caffeine degradation by using compound interest
def current_caffeine_in_body_compound_interest(intakes: List[Intake]) -> float:
    """
    Given a list of Intakes (timestamp, mg), calculate caffeine mg content in blood at current time.
    Assumes a bioavailability of 100%, immediate absorption in body, and caffeine half-life of 5 hours denoted by
    CAFFEINE_DEGRADATION_PR_HOUR.
    """
    # if no intakes withing given time interval, return 0mg in blood
    if len(intakes) == 0:
        return 0

    # init last intake time to 24 hours and one minute ago to keep degradation within scope of intakes
    last_intake_time = timezone.now() - timedelta(days=1, minutes=1)
    mg_blood = 0

    # append intake of 0 mg at timezone.now to intakes to calculate caffeine degradation from the latest intake to now
    intakes.append(Intake(timezone.now(), 0))

    # do compound interest on list of intakes
    for intake in intakes:
        # first do degradation of current caffeine in blood using compound rule (kn = k0 * (1 + r)^n), maxing to 0
        mg_blood = max(
            mg_blood
            * ((1 - CAFFEINE_DEGRADATION_PR_HOUR) ** ((intake.timestamp - last_intake_time) / timedelta(hours=1))),
            0,
        )
        # swap curr timestamp with last intake time to calculate degradation timespan in next iteration
        last_intake_time = intake.timestamp

        # finally, add current intake of caffeine to mg_blood
        mg_blood += intake.mg

    return mg_blood
