from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_mammogram, name='upload_mammogram'),
    path('process/<uuid:mammogram_id>/', views.processing_view, name='process_mammogram'),
    path('predict/<uuid:mammogram_id>/', views.predict_and_redirect_view, name='predict_and_redirect'),
    path('confusion_matrix_data/', views.get_conf_matrix_data, name='confusion_matrix_data'),
    path('results/<uuid:mammogram_id>/', views.results_view, name='results'),
    path('disapprove/<uuid:mammogram_id>/', views.results_view, name='disapprove'),
    path('approve/<uuid:mammogram_id>/', views.approve_results_view, name='approve'),
    path('diagnosis_report/<uuid:mammogram_id>/', views.generate_report_view, name='generate_report'),
    path('reports/', views.reports_view, name='reports'),
    path('reports/weekly/', views.weekly_summary_view, name='weekly_summary'),
    path('reports/detail_report/', views.detailed_reports_view, name='detailed_reports'),
    path('reports/exceptional_report/', views.exceptional_reports_view, name='exceptional_reports'),
]