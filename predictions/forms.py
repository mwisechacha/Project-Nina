from django import forms
from .models import Mammogram

class MammogramForm(forms.ModelForm):
    class Meta:
        model = Mammogram
        fields = ['image']

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            valid_extensions = ['.jpg', '.jpeg', '.png', '.npy']
            if not any(image.name.lower().endswith(ext) for ext in valid_extensions):
                raise forms.ValidationError('Only .npy, .jpeg, .jpg and .png files are allowed.')
        return image