from typing import List, Counter, Tuple

from achievements.models import (
    Achievement,
    get_new_achievements,
    get_missing_achievements,
    get_acquired_achievements_with_rarity,
    get_user_leaderboard_position,
)
from django import template
from django.conf import settings
from django.db.models import QuerySet
from stregsystem.models import Product, Member

register = template.Library()


@register.inclusion_tag('achievements/achievement_ranking.html')
def achievement_ranking(member: Member):
    acquired_achievements: List[Tuple[Achievement, float]] = get_acquired_achievements_with_rarity(member)
    missing_achievements: QuerySet[Achievement] = get_missing_achievements(member)
    achievement_progress_str: str = (
        f"{len(acquired_achievements)}/{len(acquired_achievements)+len(missing_achievements)}"
    )
    achievement_top_percentage: float = get_user_leaderboard_position(member)
    achievement_missing_icon: str = f"{settings.MEDIA_URL}stregsystem/achievement/achievement_missing.png"

    def get_color_by_rarity(rarity):
        if rarity <= 1:
            color = (243, 175, 25)  # Fortnite Orange (Legendary)
        elif rarity <= 5:
            color = (157, 77, 187)  # Fortnite Purple (Epic)
        elif rarity <= 10:
            color = (76, 81, 247)  # Fortnite Blue (Rare)
        elif rarity <= 25:
            color = (49, 146, 54)  # Fortnite Green (Common)
        else:
            color = (140, 140, 140)  # Fortnite Green (Uncommon)
        return f"rgb{color}"

    # Convert the acquired achievements to a list of tuples with rounded rarity and color
    acquired_achievements = [
        (achievement, f"{round(rarity, 2)}%", get_color_by_rarity(rarity))
        for achievement, rarity in acquired_achievements
    ]

    return {
        'acquired_achievements': acquired_achievements,
        'missing_achievements': missing_achievements,
        'achievement_progress_str': achievement_progress_str,
        'achievement_top_percentage': achievement_top_percentage,
        'achievement_missing_icon': achievement_missing_icon,
    }
