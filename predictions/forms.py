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

    # def clean_image(self):
    #     image = self.cleaned_data.get('image')
    #     if image:
    #         valid_extensions = ['.jpg', '.jpeg', '.png', '.npy']
    #         if not any(image.name.lower().endswith(ext) for ext in valid_extensions):
    #             raise forms.ValidationError('Only .npy, .jpeg, .jpg and .png files are allowed.')
    #     return image