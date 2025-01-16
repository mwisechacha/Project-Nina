from django import forms
from .models import Mammogram

class MammogramForm(forms.ModelForm):
    class Meta:
        model = Mammogram
        fields = ['image']