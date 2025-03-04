from django import forms
from .models import Mammogram, ModelMetrics, Patient

class MammogramForm(forms.ModelForm):
    class Meta:
        model = Mammogram
        fields = ['image', 'mass_margin', 'mass_shape', 'breast_density']

class ModelMetricsForm(forms.ModelForm):
    class Meta:
        model = ModelMetrics
        fields = ['model_name',
                  'target', 'accuracy', 
                  'precision','recall', 
                  'f1_score']
        
class Patient(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['first_name', 'last_name',
                   'age']

    