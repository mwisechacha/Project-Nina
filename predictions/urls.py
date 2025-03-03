from django.urls import path
from .views import upload_mammogram, processing_view, predict_and_redirect_view, results_view, generate_report_view, get_conf_matrix_data

urlpatterns = [
    path('upload/', upload_mammogram, name='upload_mammogram'),
    path('process/<uuid:mammogram_id>/', processing_view, name='process_mammogram'),
    path('predict/<uuid:mammogram_id>/', predict_and_redirect_view, name='predict_and_redirect'),
    path('confusion_matrix_data/', get_conf_matrix_data, name='confusion_matrix_data'),
    path('results/<uuid:mammogram_id>/', results_view, name='results'),
    path('report/<uuid:mammogram_id>/', generate_report_view, name='generate_report'),
]