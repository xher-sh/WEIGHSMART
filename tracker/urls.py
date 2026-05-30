from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Weight
    path('weight/', views.weight_tracker, name='weight_tracker'),
    path('weight/delete/<int:pk>/', views.delete_weight, name='delete_weight'),

    # Calories
    path('calories/', views.calorie_tracker, name='calorie_tracker'),
    path('calories/delete/<int:pk>/', views.delete_meal, name='delete_meal'),

    # Water
    path('water/', views.water_tracker, name='water_tracker'),

    # Habits
    path('habits/', views.habit_tracker, name='habit_tracker'),
    path('habits/add/', views.add_habit, name='add_habit'),
    path('habits/toggle/<int:pk>/', views.toggle_habit, name='toggle_habit'),
    path('habits/delete/<int:pk>/', views.delete_habit, name='delete_habit'),

    # Achievements
    path('achievements/', views.achievements, name='achievements'),

    # Profile
    path('profile/', views.profile, name='profile'),
]
