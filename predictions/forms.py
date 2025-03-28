from django import forms
from django.utils.timezone import now
from django.core.exceptions import ValidationError
from .models import Mammogram, ModelMetrics

def validate_image_format(image):
    valid_formats = ['image/jpeg', 'image/png']
    if image.content_type not in valid_formats:
        raise ValidationError("Invalid file format. Please upload a JPEG or PNG image.")

class MammogramForm(forms.ModelForm):
    patient_first_name = forms.CharField(max_length=100, required=True)
    patient_last_name = forms.CharField(max_length=100, required=True)
    patient_date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    image = forms.ImageField(validators=[validate_image_format])

    class Meta:
        model = Mammogram
        fields = ['image', 'mass_margin', 'mass_shape', 'breast_density']

    def clean_patient_date_of_birth(self):
        dob = self.cleaned_data.get('patient_date_of_birth')
        if dob > now().date():
            raise forms.ValidationError("Date of birth cannot be in the future.")
        return dob

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
    birads_actual = forms.ChoiceField(choices=[('0', 'Need additional imaging'), ('1', 'Negative'), ('2', 'Benign'), ('3', 'Probably benign'), ('4', 'Suspicious of malignancy'), ('5', 'Highly suggestive of malignancy')], required=True)
    comments = forms.CharField(widget=forms.Textarea, required=False)

    