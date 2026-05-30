"""
Sample data seeder for WeighSmart.
Run: python manage.py shell < seed_data.py
"""
import os, sys, django
sys.path.insert(0, '/home/claude/weighsmart')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weighsmart.settings')
django.setup()

from django.contrib.auth.models import User
from tracker.models import (UserProfile, WeightEntry, Meal, WaterIntake,
                             Habit, HabitCompletion, Achievement)
from datetime import date, timedelta

# Create demo user
if not User.objects.filter(username='demo').exists():
    user = User.objects.create_user('demo', 'demo@weighsmart.com', 'demo1234',
                                     first_name='Alex', last_name='Johnson')
    UserProfile.objects.create(
        user=user, starting_weight=88.0, target_weight=75.0,
        daily_calorie_goal=2000, daily_water_goal=8, height=175.0
    )
    print("✅ Demo user created (username: demo, password: demo1234)")
else:
    user = User.objects.get(username='demo')
    print("ℹ️  Demo user already exists")

# Weight entries — 30 days of gradual loss
for i in range(30, -1, -1):
    d = date.today() - timedelta(days=i)
    w = round(88.0 - (i * 0.15) + (0.2 if i % 3 == 0 else 0), 2)
    WeightEntry.objects.get_or_create(user=user, date=d, defaults={'weight': w})
print(f"✅ Weight entries seeded")

# Meals today
today = date.today()
meals = [
    ('Oatmeal with banana', 'breakfast', 320, 8, 60, 6),
    ('Chicken Caesar Salad', 'lunch', 450, 35, 20, 22),
    ('Protein Bar', 'snack', 200, 20, 24, 7),
    ('Grilled Salmon & Veg', 'dinner', 520, 45, 30, 18),
]
for name, mtype, cal, prot, carb, fat in meals:
    Meal.objects.get_or_create(
        user=user, name=name, date=today,
        defaults={'meal_type': mtype, 'calories': cal, 'protein': prot, 'carbs': carb, 'fat': fat}
    )
# Past meals
for i in range(1, 8):
    d = today - timedelta(days=i)
    Meal.objects.get_or_create(user=user, name='Healthy Meal', date=d,
                                defaults={'meal_type': 'lunch', 'calories': 1800 + i*50})
print("✅ Meals seeded")

# Water intake
for i in range(7):
    d = today - timedelta(days=i)
    WaterIntake.objects.get_or_create(user=user, date=d, defaults={'glasses': 8 - i % 3})
print("✅ Water intake seeded")

# Habits
habit_data = [
    ('Morning Run', '🏃', 'Run for 30 minutes every morning'),
    ('Drink Water', '💧', 'Drink 8 glasses of water'),
    ('Meditation', '🧘', 'Meditate for 10 minutes'),
    ('No Junk Food', '🥗', 'Avoid processed foods'),
    ('Sleep 8 hours', '😴', 'Get a full night of rest'),
]
created_habits = []
for name, icon, desc in habit_data:
    h, _ = Habit.objects.get_or_create(user=user, name=name,
                                        defaults={'icon': icon, 'description': desc})
    created_habits.append(h)

# Habit completions — builds streaks
for habit in created_habits:
    for i in range(10):
        d = today - timedelta(days=i)
        HabitCompletion.objects.get_or_create(habit=habit, date=d)
print("✅ Habits and completions seeded (10-day streak)")

# Achievements
Achievement.objects.get_or_create(user=user, badge_type='first_log')
Achievement.objects.get_or_create(user=user, badge_type='streak_3')
Achievement.objects.get_or_create(user=user, badge_type='streak_7')
Achievement.objects.get_or_create(user=user, badge_type='weight_loss_1')
print("✅ Achievements seeded")

print("\n🎉 All sample data loaded!")
print("   Login: username=demo  password=demo1234")
