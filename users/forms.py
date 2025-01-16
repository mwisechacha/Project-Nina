from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    organization = forms.CharField(max_length=100, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'organization', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('A user with that email already exists.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 != password2:
            raise forms.ValidationError('Passwords do not match.')
        
        return cleaned_data

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