from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, WeightEntry, Meal, WaterIntake, Habit


class RegistrationForm(UserCreationForm):
    """Extended registration form with health profile fields."""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=50, required=True)
    last_name = forms.CharField(max_length=50, required=True)
    starting_weight = forms.DecimalField(max_digits=5, decimal_places=2, required=False,
                                          label="Starting Weight (kg)")
    target_weight = forms.DecimalField(max_digits=5, decimal_places=2, required=False,
                                        label="Target Weight (kg)")
    height = forms.DecimalField(max_digits=5, decimal_places=2, required=False,
                                 label="Height (cm)")
    daily_calorie_goal = forms.IntegerField(initial=2000, min_value=500, max_value=10000,
                                             label="Daily Calorie Goal (kcal)")
    daily_water_goal = forms.IntegerField(initial=8, min_value=1, max_value=30,
                                           label="Daily Water Goal (glasses)")

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email',
                  'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                starting_weight=self.cleaned_data.get('starting_weight'),
                target_weight=self.cleaned_data.get('target_weight'),
                height=self.cleaned_data.get('height'),
                daily_calorie_goal=self.cleaned_data.get('daily_calorie_goal', 2000),
                daily_water_goal=self.cleaned_data.get('daily_water_goal', 8),
            )
        return user


class WeightEntryForm(forms.ModelForm):
    """Form for logging daily weight."""
    class Meta:
        model = WeightEntry
        fields = ['weight', 'date', 'notes']
        widgets = {
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 72.5', 'step': '0.1'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional notes...'}),
        }


class MealForm(forms.ModelForm):
    """Form for logging meals and calories."""
    class Meta:
        model = Meal
        fields = ['name', 'meal_type', 'calories', 'protein', 'carbs', 'fat', 'date']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Chicken Salad'}),
            'meal_type': forms.Select(attrs={'class': 'form-select'}),
            'calories': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'kcal', 'min': '0'}),
            'protein': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'g', 'step': '0.1', 'min': '0'}),
            'carbs': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'g', 'step': '0.1', 'min': '0'}),
            'fat': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'g', 'step': '0.1', 'min': '0'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class WaterIntakeForm(forms.ModelForm):
    """Form for logging water glasses."""
    class Meta:
        model = WaterIntake
        fields = ['glasses', 'date']
        widgets = {
            'glasses': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '30', 'value': '1'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class HabitForm(forms.ModelForm):
    """Form for creating and editing habits."""
    ICON_CHOICES = [
        ('✅', '✅ Checkmark'), ('🏃', '🏃 Running'), ('💪', '💪 Workout'),
        ('🥗', '🥗 Healthy Eating'), ('💧', '💧 Hydration'), ('😴', '😴 Sleep'),
        ('🧘', '🧘 Meditation'), ('📚', '📚 Reading'), ('🚶', '🚶 Walking'),
        ('🍎', '🍎 Nutrition'), ('☀️', '☀️ Morning Routine'), ('🌙', '🌙 Night Routine'),
    ]
    icon = forms.ChoiceField(choices=ICON_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = Habit
        fields = ['name', 'description', 'icon', 'frequency']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Morning Run'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2,
                                                  'placeholder': 'Describe your habit...'}),
            'frequency': forms.Select(attrs={'class': 'form-select'}),
        }


class ProfileUpdateForm(forms.ModelForm):
    """Form for updating user health profile."""
    class Meta:
        model = UserProfile
        fields = ['target_weight', 'starting_weight', 'daily_calorie_goal', 'daily_water_goal', 'height']
        widgets = {
            'target_weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'starting_weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'daily_calorie_goal': forms.NumberInput(attrs={'class': 'form-control'}),
            'daily_water_goal': forms.NumberInput(attrs={'class': 'form-control'}),
            'height': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
        }
