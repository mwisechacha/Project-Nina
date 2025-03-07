from django import forms
from .models import Mammogram, ModelMetrics

class MammogramForm(forms.ModelForm):
    patient_first_name = forms.CharField(max_length=100, required=True)
    patient_last_name = forms.CharField(max_length=100, required=True)
    patient_age = forms.IntegerField(required=True)

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
        

    