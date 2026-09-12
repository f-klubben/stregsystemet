# Achievements

An achievement is a milestone which is stored in the database for the individual member.

# Achievements database structure

`Achievement` defines an achievement with a title, description, and icon. 
You can set either Active From or Active Duration to specify when tracking begins. 
Linked to one or more tasks that specify the criteria to earn the achievement, plus optional constraints.

`AchievementConstraint` Optional time-based restrictions (e.g., date, time, weekday).
Useful for limiting when an achievement can be completed.

`AchievementTask` Defines the requirements a user must meet to earn the achievement.
Includes a goal and a task type (e.g., purchase a specific product, buy from a category, consume a certain amount of alcohol, etc.).

`AchievementComplete` Records when a member completes an achievement.
Each member can complete an achievement only once.

## How to Add an Achievement

### What Achievements Can Track

- Purchases of specific products or categories
- Any purchase in general
- Amounts of alcohol or caffeine consumed
- Used or remaining funds

### Optional Constraints

- Specific months, days, times, or weekdays for completion

### Steps to Add and Achievement

1. Log in to the Admin panel:

    - Admin panel: <http://127.0.0.1:8000/admin/>  
    - Login: `tester:treotreo` 

2. If needed, create new AchievementTask entries that fit your criteria.
3. Create an Achievement entry and link it to one or more tasks.
4. (Optional) Add AchievementConstraint entries to enforce time-based restrictions.

### Adding Custom Logic

For achievements requiring unique behavior:

- Add a new task_type in the AchievementTask model.
- Implement the corresponding logic in the model functions.
- Update the _filter_relevant_sales() function to handle the new task type.