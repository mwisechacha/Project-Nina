from django.db import models
import uuid

# class Patient(models.Model):
#     patient_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     name = models.CharField(max_length=100)
#     age = models.IntegerField()

#     def __str__(self):
#         return f"Patient {self.name} with ID {self.patient_id}"


class Mammogram(models.Model):
    # patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    image_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    image = models.ImageField(upload_to='prediction/images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    model_diagnosis = models.CharField(max_length=100, blank=True, null=True)
    mass_margin = models.CharField(max_length=100, blank=True, null=True)
    mass_shape = models.CharField(max_length=100, blank=True, null=True)
    breast_density = models.CharField(max_length=100, blank=True, null=True)
    descriptive_diagnosis = models.CharField(max_length=100, blank=True, null=True)
    birads_assessment = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Mammogram for Patient {self.image_id} uploaded at {self.uploaded_at}"
    
class ModelMetrics(models.Model):
    model_name = models.CharField(max_length=100)
    target = models.IntegerField()
    accuracy = models.FloatField(blank=True, null=True)
    precision = models.FloatField(blank=True, null=True)
    recall = models.FloatField(blank=True, null=True)
    f1_score = models.FloatField(blank=True, null=True)

    def __str__(self):
        return f"Metrics for {self.model_name}"
    
class GroundTruth(models.Model):
    image_id = models.CharField(max_length=255, unique=True)
    label = models.IntegerField() 

    def __str__(self):
        return f"{self.image_id} {'Benign' if self.label == 0 else 'Malignant'}"

