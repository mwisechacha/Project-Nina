from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Profile
from predictions.models import Radiologist

class RegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=100, required=False)
    last_name = forms.CharField(max_length=100, required=False)
    email = forms.EmailField(required=True)
    organization = forms.CharField(max_length=100, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'organization', 'password1', 'password2']

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
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get('email')
        if commit:
            user.save()
            Profile.objects.create(
                user=user,
                first_name=self.cleaned_data.get('first_name'),
                last_name=self.cleaned_data.get('last_name'),
                organization=self.cleaned_data.get('organization')
            )
            Radiologist.objects.create(user=user)

        return user


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