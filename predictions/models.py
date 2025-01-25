from django.db import models
import uuid

# Create your models here.
class Mammogram(models.Model):
    image_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    image = models.ImageField(upload_to='prediction/images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    model_diagnosis = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Mammogram for Patient {self.image_id} uploaded at {self.uploaded_at}"
    
class GroundTruth(models.Model):
    image_id = models.CharField(max_length=255, unique=True)
    label = models.IntegerField() 

    def __str__(self):
        return f"{self.image_id} {'Benign' if self.label == 0 else 'Malignant'}"

