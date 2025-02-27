from django.contrib import admin
from .models import Mammogram, ModelMetrics, GroundTruth, Patient

@admin.register(ModelMetrics)
class ModelMetricsAdmin(admin.ModelAdmin):
    list_display = ['model_name', 'target', 'accuracy', 
                    'precision', 'recall', 'f1_score']
    
@admin.register(Mammogram)
class MammogramAdmin(admin.ModelAdmin):
    list_display = ['image_id', 'uploaded_at', 'model_diagnosis', 'mass_margin', 'mass_shape', 'breast_density']

admin.site.register(GroundTruth)
admin.site.register(Patient)