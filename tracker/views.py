from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.db.models import Sum, Avg
from django.utils import timezone
from datetime import date, timedelta
import json

from .models import (UserProfile, WeightEntry, Meal, WaterIntake,
                     Habit, HabitCompletion, Achievement)
from .forms import (RegistrationForm, WeightEntryForm, MealForm,
                    WaterIntakeForm, HabitForm, ProfileUpdateForm)


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def check_and_award_achievements(user):
    """Check conditions and award any newly earned badges."""
    profile, _ = UserProfile.objects.get_or_create(user=user)

    # First weight log
    if WeightEntry.objects.filter(user=user).count() >= 1:
        Achievement.objects.get_or_create(user=user, badge_type='first_log')

    # Weight loss milestones
    first_entry = WeightEntry.objects.filter(user=user).order_by('date').first()
    latest_entry = WeightEntry.objects.filter(user=user).order_by('-date').first()
    if first_entry and latest_entry and first_entry != latest_entry:
        loss = float(first_entry.weight) - float(latest_entry.weight)
        if loss >= 1:
            Achievement.objects.get_or_create(user=user, badge_type='weight_loss_1')
        if loss >= 5:
            Achievement.objects.get_or_create(user=user, badge_type='weight_loss_5')
        if loss >= 10:
            Achievement.objects.get_or_create(user=user, badge_type='weight_loss_10')

    # Goal reached
    if (profile.target_weight and latest_entry and
            float(latest_entry.weight) <= float(profile.target_weight)):
        Achievement.objects.get_or_create(user=user, badge_type='goal_reached')

    # Habit streaks (check across all habits)
    for habit in Habit.objects.filter(user=user, is_active=True):
        streak = habit.get_current_streak()
        if streak >= 3:
            Achievement.objects.get_or_create(user=user, badge_type='streak_3')
        if streak >= 7:
            Achievement.objects.get_or_create(user=user, badge_type='streak_7')
        if streak >= 30:
            Achievement.objects.get_or_create(user=user, badge_type='streak_30')


# ──────────────────────────────────────────────
# Auth Views
# ──────────────────────────────────────────────

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to WeighSmart, {user.first_name}! 🎉")
            return redirect('dashboard')
    else:
        form = RegistrationForm()
    return render(request, 'auth/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}! 💪")
            return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'auth/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You've been logged out. Stay healthy! 🌿")
    return redirect('login')


# ──────────────────────────────────────────────
# Dashboard
# ──────────────────────────────────────────────

@login_required
def dashboard(request):
    user = request.user
    today = date.today()
    profile, _ = UserProfile.objects.get_or_create(user=user)

    # Current weight
    latest_weight = WeightEntry.objects.filter(user=user).order_by('-date').first()

    # Calories today
    today_calories = Meal.objects.filter(user=user, date=today).aggregate(
        total=Sum('calories'))['total'] or 0

    # Water today
    today_water = WaterIntake.objects.filter(user=user, date=today).aggregate(
        total=Sum('glasses'))['total'] or 0

    # Habits summary
    habits = Habit.objects.filter(user=user, is_active=True)
    habits_completed_today = sum(1 for h in habits if h.is_completed_today())

    # Recent achievements
    recent_achievements = Achievement.objects.filter(user=user).order_by('-earned_at')[:4]

    # Weight trend (last 7 days)
    week_ago = today - timedelta(days=6)
    weight_history = WeightEntry.objects.filter(
        user=user, date__gte=week_ago).order_by('date')

    check_and_award_achievements(user)

    context = {
        'profile': profile,
        'latest_weight': latest_weight,
        'today_calories': today_calories,
        'today_water': today_water,
        'water_goal': profile.daily_water_goal,
        'calorie_goal': profile.daily_calorie_goal,
        'habits': habits,
        'habits_completed_today': habits_completed_today,
        'total_habits': habits.count(),
        'recent_achievements': recent_achievements,
        'progress_pct': profile.get_progress_percentage(),
        'water_pct': min(100, round((today_water / profile.daily_water_goal) * 100)) if profile.daily_water_goal else 0,
        'calorie_pct': min(100, round((today_calories / profile.daily_calorie_goal) * 100)) if profile.daily_calorie_goal else 0,
    }
    return render(request, 'dashboard.html', context)


# ──────────────────────────────────────────────
# Weight Tracker
# ──────────────────────────────────────────────

@login_required
def weight_tracker(request):
    user = request.user
    if request.method == 'POST':
        form = WeightEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.user = user
            try:
                entry.save()
                check_and_award_achievements(user)
                messages.success(request, f"Weight {entry.weight}kg logged for {entry.date} ✅")
            except Exception:
                messages.error(request, "You already have a weight entry for that date.")
            return redirect('weight_tracker')
    else:
        form = WeightEntryForm()

    entries = WeightEntry.objects.filter(user=user).order_by('-date')[:30]

    # Chart data
    chart_entries = list(reversed(list(entries)))
    chart_labels = [str(e.date) for e in chart_entries]
    chart_data = [float(e.weight) for e in chart_entries]

    context = {
        'form': form,
        'entries': entries,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
    }
    return render(request, 'weight/tracker.html', context)


@login_required
def delete_weight(request, pk):
    entry = get_object_or_404(WeightEntry, pk=pk, user=request.user)
    entry.delete()
    messages.success(request, "Weight entry deleted.")
    return redirect('weight_tracker')


# ──────────────────────────────────────────────
# Calorie Tracker
# ──────────────────────────────────────────────

@login_required
def calorie_tracker(request):
    user = request.user
    today = date.today()

    if request.method == 'POST':
        form = MealForm(request.POST)
        if form.is_valid():
            meal = form.save(commit=False)
            meal.user = user
            meal.save()
            messages.success(request, f"'{meal.name}' logged — {meal.calories} kcal 🥗")
            return redirect('calorie_tracker')
    else:
        form = MealForm(initial={'date': today})

    # Today's meals
    today_meals = Meal.objects.filter(user=user, date=today)
    today_total = today_meals.aggregate(total=Sum('calories'))['total'] or 0

    # Macro breakdown
    macros = today_meals.aggregate(
        total_protein=Sum('protein'),
        total_carbs=Sum('carbs'),
        total_fat=Sum('fat'),
    )

    profile, _ = UserProfile.objects.get_or_create(user=user)

    # 7-day history for chart
    week_ago = today - timedelta(days=6)
    daily_totals = []
    date_labels = []
    for i in range(7):
        d = week_ago + timedelta(days=i)
        total = Meal.objects.filter(user=user, date=d).aggregate(
            total=Sum('calories'))['total'] or 0
        daily_totals.append(total)
        date_labels.append(d.strftime('%a'))

    context = {
        'form': form,
        'today_meals': today_meals,
        'today_total': today_total,
        'calorie_goal': profile.daily_calorie_goal,
        'calorie_pct': min(100, round((today_total / profile.daily_calorie_goal) * 100)) if profile.daily_calorie_goal else 0,
        'macros': macros,
        'chart_labels': json.dumps(date_labels),
        'chart_data': json.dumps(daily_totals),
        'chart_goal': profile.daily_calorie_goal,
    }
    return render(request, 'calories/tracker.html', context)


@login_required
def delete_meal(request, pk):
    meal = get_object_or_404(Meal, pk=pk, user=request.user)
    meal.delete()
    messages.success(request, "Meal deleted.")
    return redirect('calorie_tracker')


# ──────────────────────────────────────────────
# Water Tracker
# ──────────────────────────────────────────────

@login_required
def water_tracker(request):
    user = request.user
    today = date.today()

    if request.method == 'POST':
        form = WaterIntakeForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.user = user
            entry.save()
            messages.success(request, f"💧 {entry.glasses} glass(es) logged!")
            return redirect('water_tracker')
    else:
        form = WaterIntakeForm(initial={'date': today})

    profile, _ = UserProfile.objects.get_or_create(user=user)
    today_water = WaterIntake.objects.filter(user=user, date=today).aggregate(
        total=Sum('glasses'))['total'] or 0
    history = WaterIntake.objects.filter(user=user).order_by('-date')[:14]

    context = {
        'form': form,
        'today_water': today_water,
        'water_goal': profile.daily_water_goal,
        'water_pct': min(100, round((today_water / profile.daily_water_goal) * 100)) if profile.daily_water_goal else 0,
        'history': history,
    }
    return render(request, 'water/tracker.html', context)


# ──────────────────────────────────────────────
# Habit Tracker
# ──────────────────────────────────────────────

@login_required
def habit_tracker(request):
    user = request.user
    today = date.today()

    habits = Habit.objects.filter(user=user, is_active=True)
    habits_with_status = []
    for habit in habits:
        habits_with_status.append({
            'habit': habit,
            'completed_today': habit.is_completed_today(),
            'streak': habit.get_current_streak(),
        })

    context = {
        'habits_with_status': habits_with_status,
        'today': today,
    }
    return render(request, 'habits/tracker.html', context)


@login_required
def add_habit(request):
    if request.method == 'POST':
        form = HabitForm(request.POST)
        if form.is_valid():
            habit = form.save(commit=False)
            habit.user = request.user
            habit.save()
            messages.success(request, f"Habit '{habit.name}' created! 🎯")
            return redirect('habit_tracker')
    else:
        form = HabitForm()
    return render(request, 'habits/add_habit.html', {'form': form})


@login_required
def toggle_habit(request, pk):
    habit = get_object_or_404(Habit, pk=pk, user=request.user)
    today = date.today()
    completion, created = HabitCompletion.objects.get_or_create(habit=habit, date=today)
    if not created:
        completion.delete()
        messages.info(request, f"'{habit.name}' unmarked for today.")
    else:
        messages.success(request, f"'{habit.name}' completed! 🎉")
    check_and_award_achievements(request.user)
    return redirect('habit_tracker')


@login_required
def delete_habit(request, pk):
    habit = get_object_or_404(Habit, pk=pk, user=request.user)
    habit.is_active = False
    habit.save()
    messages.success(request, f"Habit '{habit.name}' archived.")
    return redirect('habit_tracker')


# ──────────────────────────────────────────────
# Achievements
# ──────────────────────────────────────────────

@login_required
def achievements(request):
    user = request.user
    check_and_award_achievements(user)
    earned = Achievement.objects.filter(user=user)
    earned_types = earned.values_list('badge_type', flat=True)

    all_badges = [
        {'type': bt, 'name': bn, 'icon': Achievement.BADGE_ICONS.get(bt, '🏅'),
         'earned': bt in earned_types}
        for bt, bn in Achievement.BADGE_TYPES
    ]
    context = {
        'all_badges': all_badges,
        'earned_count': earned.count(),
        'total_count': len(Achievement.BADGE_TYPES),
    }
    return render(request, 'achievements.html', context)


# ──────────────────────────────────────────────
# Profile
# ──────────────────────────────────────────────

@login_required
def profile(request):
    user = request.user
    profile_obj, _ = UserProfile.objects.get_or_create(user=user)
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=profile_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully! ✅")
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=profile_obj)
    return render(request, 'profile.html', {'form': form, 'profile': profile_obj})
