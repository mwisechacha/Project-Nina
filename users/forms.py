from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class LoginForm(AuthenticationForm):
    pass


class RequestDemoForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    reason = forms.ChoiceField(choices=[('learn-more', 'Learn More'), ('try-it', 'Try it out')])
    interest = forms.ChoiceField(choices=[
        ('machine-learning', 'Machine Learning'),
        ('data-analysis', 'Data Analysis'),
        ('healthcare', 'Healthcare'),
    ])