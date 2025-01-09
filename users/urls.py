from django.urls import path
from .views import register_view, home_view, login_view, logout_view, request_demo_view

urlpatterns = [
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('request-demo/', request_demo_view, name='request_demo'),
    path('', home_view, name='home'),
]