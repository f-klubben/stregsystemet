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
    if len(intakes) == 0:
        return 0

    temp_time = timezone.now() - timedelta(days=1)
    mg_blood = 0

    # append intake of 0 mg at timezone.now to intakes
    intakes.append(Intake(timezone.now(), 0))
    # do compound interest on intake list
    for intake in intakes:
        # first do degradation of current mg_blood using compound rule (kn = k0 * (1 + r)^n)
        mg_blood = max(
            mg_blood * ((1 - CAFFEINE_DEGRADATION_PR_HOUR) ** ((intake.timestamp - temp_time) / timedelta(hours=1))), 0
        )
        # swap curr timestamp with temp timestamp
        temp_time = intake.timestamp
        # then add next intake to mg_blood
        mg_blood += intake.mg

    return mg_blood
