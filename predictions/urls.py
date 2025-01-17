from django.urls import path
from .views import upload_mammogram, processing_view, results_view

urlpatterns = [
    path('upload/', upload_mammogram, name='upload_mammogram'),
    path('process/<uuid:mammogram_id>/', processing_view, name='process_mammogram'),
    path('results/<uuid:mammogram_id>/', results_view, name='results'),
]