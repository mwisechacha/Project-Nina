from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import PasswordResetConfirmView
from .views import register_view, home_view, request_demo_view, CustomLoginView, debug_password_reset_confirm

class DebugPasswordResetConfirmView(PasswordResetConfirmView):
    def dispatch(self, request, *args, **kwargs):
        print(f"DEBUG: password_reset_confirm called with UID: {kwargs.get('uidb64')}, Token: {kwargs.get('token')}")
        return super().dispatch(request, *args, **kwargs)

urlpatterns = [
    path('register/', register_view, name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='users/password_reset.html',
        email_template_name='users/password_reset_email.html',
        subject_template_name='users/password_reset_subject.txt'
        ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='users/password_reset_done.html'
    ), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='users/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='users/password_reset_complete.html'
    ), name='password_reset_complete'),
    path('debug-password-reset-confirm/<uidb64>/<token>/', debug_password_reset_confirm),
    path('request-demo/', request_demo_view, name='request_demo'),
    path('', home_view, name='home'),
]