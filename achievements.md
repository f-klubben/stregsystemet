# Achievements

An achievement is a milestone which is stored in the database for the individual member.

# Achievements database structure

`Achievement` defines an achievement with a title, description, icon, and optional timing rules.
Only one of begin_at or duration can be set.

`AchievementConstraint` is an optional time-based restrictions (e.g., date, time, weekday) tied to an achievement.
Useful for limiting when an achievement can be completed.

`AchievementTask` defines what a user must do to earn an achievement. Linked to a product, category, alcohol_content, or caffeine_content — only one of these may be set.
Supports different task types like spending/remaining funds.

`AchievementComplete` tracks when a member completes an achievement. Each member can only complete an achievement once.

## How to Add an Achievement

### What Achievements Can Track

- Product or category purchase amounts
- Used or remaining funds
- Alcohol or caffeine content

### Optional Constraints

- Specific months, days, times, or weekdays for completion

### Steps to Add and Achievement

1. Log in to the Admin panel:

    - Admin panel: <http://127.0.0.1:8000/admin/>  
    - Login: `tester:treotreo` 

2. Create a new Achievement
3. Add one or more AchievementTask entries linked to that achievement
4. (*Optional*) Add AchievementConstraint entries if you want time-based restrictions

### Adding Custom Logic

For achievements with unique behavior, add a new task_type in AchievementTask and implement the logic in achievements.py.

## Achievement Ideas
* Quite the bartender: Pomster = Limfjordsporter + Monster
* Keeper of secrets: buy a fytteturs billet.
* Ægte Datalog: buy a limfjordsporter
* Exam Week Warrior – Buy 3 energy drinks or coffees during exam month