from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

class RegisterForm(UserCreationForm):
    full_name = forms.CharField(max_length=100, required=True)
    # last_name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    organization = forms.CharField(max_length=100, required=True)

    class Meta:
        model = User
        fields = ['full_name', 'email', 'organization', 'password1', 'password2']

    def clean(self):
        cleaned_data = super().clean()
        full_name = cleaned_data.get('full_name')
        if full_name:
            first_name, last_name = self.split_full_name(full_name)
            cleaned_data['first_name'] = first_name
            cleaned_data['last_name'] = last_name
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 != password2:
            raise forms.ValidationError('Passwords do not match.')
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user
    
    def split_full_name(self, full_name):
        parts = full_name.split(' ')
        first_name = parts[0]
        last_name = ' '.join(parts[1:]) if len(parts) > 1 else ''
        return first_name, last_name

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