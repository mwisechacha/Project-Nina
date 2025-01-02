from django.urls import path
from .views import home, register_view, home_view, login_view

urlpatterns = [
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('', home_view, name='home'),
]