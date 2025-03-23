from django.contrib.auth.models import User
from django.db import models

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    organization = models.CharField(max_length=100, blank=True, null=True)


    def __str__(self):
        return f"Radiologist {self.user.username}"
    
class DemoRequest(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    reason = models.CharField(max_length=50, choices=[('learn-more', 'Learn more'),
                                                      ('try-it-out', 'Try it out')])
    interest = models.CharField(max_length=50, choices=[
        ('machine-learning', 'Machine Learning'),
        ('data-analysis', 'Data Analysis'),
        ('healthcare', 'Healthcare'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Demo request from {self.name}"