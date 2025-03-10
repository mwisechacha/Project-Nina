from django import forms
from .models import Mammogram, ModelMetrics

class MammogramForm(forms.ModelForm):
    patient_first_name = forms.CharField(max_length=100, required=True)
    patient_last_name = forms.CharField(max_length=100, required=True)
    patient_date_of_birth = forms.DateField(required=True)

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
        
class DisapproveForm(forms.Form):
    pathology_actual = forms.ChoiceField(choices=[('benign', 'Benign'), ('malignant', 'Malignant')], required=True)
    descriptive_actual = forms.ChoiceField(choices=[('bening', 'Benign'), ('malignant', 'Malignant')], required=True)
    birads_actual = forms.ChoiceField(choices=[('0', 'Need additional imaging'), ('1', 'Negative'), ('2', 'Benign'), ('3', 'Probably benign'), ('4', 'Suspicious'), ('5', 'Highly suggestive of malignancy')], required=True)
    comments = forms.CharField(widget=forms.Textarea, required=False)

    