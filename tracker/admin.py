from django.contrib import admin
from .models import UserProfile, WeightEntry, Meal, WaterIntake, Habit, HabitCompletion, Achievement


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'starting_weight', 'target_weight', 'daily_calorie_goal', 'daily_water_goal']
    search_fields = ['user__username', 'user__email']


@admin.register(WeightEntry)
class WeightEntryAdmin(admin.ModelAdmin):
    list_display = ['user', 'weight', 'date', 'created_at']
    list_filter = ['date', 'user']
    search_fields = ['user__username']
    date_hierarchy = 'date'


@admin.register(Meal)
class MealAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'meal_type', 'calories', 'date']
    list_filter = ['meal_type', 'date']
    search_fields = ['user__username', 'name']


@admin.register(WaterIntake)
class WaterIntakeAdmin(admin.ModelAdmin):
    list_display = ['user', 'glasses', 'date']
    list_filter = ['date']


@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'frequency', 'is_active', 'created_at']
    list_filter = ['is_active', 'frequency']
    search_fields = ['user__username', 'name']


@admin.register(HabitCompletion)
class HabitCompletionAdmin(admin.ModelAdmin):
    list_display = ['habit', 'date', 'created_at']
    list_filter = ['date']


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['user', 'badge_type', 'earned_at']
    list_filter = ['badge_type']
    search_fields = ['user__username']
