from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.timezone import now
from django.conf import settings
from datetime import date
import uuid

class Radiologist(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    @property
    def organization(self):
        return self.user.organization

    def __str__(self):
        return f"Radiologist {self.user.username}"


class Patient(models.Model):
    patient_id = models.CharField(max_length=20, unique=True, blank=True, null=False)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.patient_id:  
            self.patient_id = f"nina_{uuid.uuid4().hex[:8]}" 
        super().save(*args, **kwargs)  # Save the patient

    def __str__(self):
        return f"Patient {self.patient_id} ({self.first_name} {self.last_name})"
    
    def age(self):
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None
    


class Mammogram(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='mammograms', default=None)
    radiologist = models.ForeignKey(Radiologist, on_delete=models.SET_NULL, null=True, blank=True, related_name='mammograms')
    image_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    image = models.ImageField(upload_to='prediction/images/')
    uploaded_at = models.DateTimeField(default=timezone.now)
    model_diagnosis = models.CharField(max_length=100, blank=True, null=True)
    mass_margin = models.CharField(max_length=100, blank=True, null=True)
    mass_shape = models.CharField(max_length=100, blank=True, null=True)
    breast_density = models.CharField(max_length=100, blank=True, null=True)
    descriptive_diagnosis = models.CharField(max_length=100, blank=True, null=True)
    birads_assessment = models.CharField(max_length=100, blank=True, null=True)
    probability_of_cancer = models.IntegerField(blank=True, null=True)
    approved = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.uploaded_at:
            self.uploaded_at = timezone.now()
        super(Mammogram, self).save(*args, **kwargs)

    def __str__(self):
        return f"Mammogram for Patient {self.image_id} uploaded at {self.uploaded_at}"
    
class DisapprovedMammogram(models.Model):
    mammogram = models.OneToOneField(Mammogram, on_delete=models.CASCADE, related_name='disapproved_mammograms')
    pathology_actual = models.CharField(max_length=100, blank=True, null=True)
    descriptive_actual = models.CharField(max_length=100, blank=True, null=True)
    birads_actual = models.CharField(max_length=100, blank=True, null=True)
    comments = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Disapproved Mammogram for Patient {self.mammogram.image_id}"
    
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
    
class WeeklySummary(models.Model):
    week_start = models.DateField()
    week_end = models.DateField()
    total_patients = models.IntegerField(default=0)
    benign_cases = models.IntegerField(default=0)
    malignant_cases = models.IntegerField(default=0)
    radiologist = models.ForeignKey(Radiologist, on_delete=models.CASCADE, null=True, related_name='weekly_summaries', default=None)


    def __str__(self):
        return f"Summary for {self.week_start} to {self.week_end}"

