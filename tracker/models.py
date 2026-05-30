from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date


class UserProfile(models.Model):
    """Extended user profile storing health goals and preferences."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    target_weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                        help_text="Target weight in kg")
    starting_weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                          help_text="Starting weight in kg")
    daily_calorie_goal = models.PositiveIntegerField(default=2000)
    daily_water_goal = models.PositiveIntegerField(default=8, help_text="Glasses of water per day")
    height = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                  help_text="Height in cm")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def get_progress_percentage(self):
        """Calculate weight loss progress as a percentage."""
        if not self.starting_weight or not self.target_weight:
            return 0
        latest = WeightEntry.objects.filter(user=self.user).order_by('-date').first()
        if not latest:
            return 0
        start = float(self.starting_weight)
        target = float(self.target_weight)
        current = float(latest.weight)
        if start == target:
            return 100
        total_loss_needed = start - target
        loss_achieved = start - current
        if total_loss_needed <= 0:
            return 0
        pct = (loss_achieved / total_loss_needed) * 100
        return max(0, min(100, round(pct, 1)))


class WeightEntry(models.Model):
    """Daily weight measurements."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weight_entries')
    weight = models.DecimalField(max_digits=5, decimal_places=2, help_text="Weight in kg")
    date = models.DateField(default=date.today)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        unique_together = ['user', 'date']

    def __str__(self):
        return f"{self.user.username} - {self.weight}kg on {self.date}"


class Meal(models.Model):
    """Individual meal entries for calorie tracking."""
    MEAL_TYPES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('snack', 'Snack'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meals')
    name = models.CharField(max_length=200)
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPES, default='snack')
    calories = models.PositiveIntegerField()
    protein = models.DecimalField(max_digits=6, decimal_places=2, default=0, help_text="Grams")
    carbs = models.DecimalField(max_digits=6, decimal_places=2, default=0, help_text="Grams")
    fat = models.DecimalField(max_digits=6, decimal_places=2, default=0, help_text="Grams")
    date = models.DateField(default=date.today)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.name} ({self.calories} kcal)"


class WaterIntake(models.Model):
    """Daily water intake tracking."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='water_intakes')
    glasses = models.PositiveIntegerField(default=1)
    date = models.DateField(default=date.today)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.username} - {self.glasses} glasses on {self.date}"


class Habit(models.Model):
    """User-defined habits to track daily."""
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='habits')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, default='daily')
    icon = models.CharField(max_length=50, default='✅')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.user.username} - {self.name}"

    def get_current_streak(self):
        """Calculate the current consecutive-day completion streak."""
        completions = HabitCompletion.objects.filter(
            habit=self
        ).order_by('-date').values_list('date', flat=True)
        if not completions:
            return 0
        streak = 0
        check_date = date.today()
        for comp_date in completions:
            if comp_date == check_date:
                streak += 1
                check_date = date(check_date.year, check_date.month, check_date.day)
                from datetime import timedelta
                check_date = check_date - timedelta(days=1)
            else:
                break
        return streak

    def is_completed_today(self):
        return HabitCompletion.objects.filter(habit=self, date=date.today()).exists()


class HabitCompletion(models.Model):
    """Records each time a habit is marked complete."""
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE, related_name='completions')
    date = models.DateField(default=date.today)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['habit', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.habit.name} completed on {self.date}"


class Achievement(models.Model):
    """Badges and milestones awarded to users."""
    BADGE_TYPES = [
        ('streak_3', '3-Day Streak'),
        ('streak_7', '7-Day Streak'),
        ('streak_30', '30-Day Streak'),
        ('weight_loss_1', 'Lost 1 kg'),
        ('weight_loss_5', 'Lost 5 kg'),
        ('weight_loss_10', 'Lost 10 kg'),
        ('calorie_week', 'On Target 7 Days'),
        ('water_week', 'Hydrated 7 Days'),
        ('first_log', 'First Weight Log'),
        ('goal_reached', 'Goal Reached!'),
    ]
    BADGE_ICONS = {
        'streak_3': '🔥',
        'streak_7': '⚡',
        'streak_30': '🏆',
        'weight_loss_1': '⭐',
        'weight_loss_5': '🌟',
        'weight_loss_10': '💎',
        'calorie_week': '🥗',
        'water_week': '💧',
        'first_log': '📝',
        'goal_reached': '🎯',
    }
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    badge_type = models.CharField(max_length=30, choices=BADGE_TYPES)
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'badge_type']
        ordering = ['-earned_at']

    def __str__(self):
        return f"{self.user.username} - {self.get_badge_type_display()}"

    def get_icon(self):
        return self.BADGE_ICONS.get(self.badge_type, '🏅')
