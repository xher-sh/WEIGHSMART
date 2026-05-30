from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('dashboard' if request.user.is_authenticated else 'login'), name='home'),
    path('', include('tracker.urls')),
]
