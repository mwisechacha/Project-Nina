from django.db import models
import uuid

# Create your models here.
class Mammogram(models.Model):
    image_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    image = models.ImageField(upload_to='prediction/images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Mammogram for Patient {self.image_id} uploaded at {self.uploaded_at}"
    

