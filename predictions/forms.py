from django import forms
from .models import Mammogram, ModelMetrics

class MammogramForm(forms.ModelForm):
    class Meta:
        model = Mammogram
        fields = ['image', 'mass_margin', 'mass_shape', 'breast_density']

class ModelMetricsForm(forms.ModelForm):
    class Meta:
        model = ModelMetrics
        fields = ['model_name', 'accuracy', 'precision', 'recall', 'f1_score']