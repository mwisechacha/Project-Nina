from io import BytesIO
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.urls import reverse
from django.template.loader import render_to_string
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils.timezone import now, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_RIGHT
from .forms import MammogramForm
from .models import Mammogram, ModelMetrics, Patient, WeeklySummary, Radiologist
from .predictions import predict, get_mammogram_stats
from .descriptive_predictions import describe_predict
from .utils import get_conf_matrix_data
import os

def upload_mammogram(request):
    image_id = request.GET.get('image_id')
    if request.method == 'POST':
        mammogram_form = MammogramForm(request.POST, request.FILES)
        if mammogram_form.is_valid():
            first_name = request.POST.get('patient_first_name')
            last_name = request.POST.get('patient_last_name')
            age = request.POST.get('patient_age')
            patient, created = Patient.objects.get_or_create(
                first_name=first_name, last_name=last_name, defaults={'age': age}
            )
            try:
                radiologist = Radiologist.objects.get(user=request.user)
            except ObjectDoesNotExist:
                radiologist = Radiologist.objects.create(user=request.user)  
            mammogram = mammogram_form.save(commit=False)
            mammogram.patient = patient
            mammogram.radiologist = radiologist
            mammogram.save()
            print(mammogram.patient)
            return HttpResponseRedirect(reverse('process_mammogram', args=[mammogram.image_id]))
        else:
            print(mammogram_form.errors)
    else:
        if image_id:
            image_path = os.path.join(settings.MEDIA_ROOT, 'images', f'images/mammograms/{image_id}.jpg')
            if os.path.exists(image_path):
                with open(image_path, 'rb') as f:
                    mammogram_form = MammogramForm({'image': f})
            else:
                mammogram_form = MammogramForm()
        else:
            mammogram_form = MammogramForm()
    return render(request, 'predictions/upload_image.html', {'mammogram_form': mammogram_form})

def processing_view(request, mammogram_id):
    mammogram = get_object_or_404(Mammogram, pk=mammogram_id)
    results_url = reverse('predict_and_redirect', args=[mammogram.image_id])
    return render(request, 'predictions/process_image.html', {'mammogram_id': mammogram_id, 'results_url': results_url})

def predict_and_redirect_view(request, mammogram_id):
    mammogram = get_object_or_404(Mammogram, pk=mammogram_id)

    # predictions based on the image
    prediction_result = predict(mammogram.image.path)
    mammogram.model_diagnosis = prediction_result

    # predictions based on mass attributes
    mass_margin = mammogram.mass_margin
    mass_shape = mammogram.mass_shape
    breast_density = mammogram.breast_density
    describe_prediction, birads_prediction, probability_of_cancer = describe_predict(mass_margin, mass_shape, breast_density)
    mammogram.descriptive_diagnosis = describe_prediction
    mammogram.birads_assessment = birads_prediction
    mammogram.probability_of_cancer = probability_of_cancer


    mammogram.save()
    print(mammogram.descriptive_diagnosis)
    print(mammogram.birads_assessment)

    return HttpResponseRedirect(reverse('results', args=[mammogram.image_id]))

def confusion_matrix_data(request):
    data = get_conf_matrix_data()
    return JsonResponse(data)
    

def results_view(request, mammogram_id):
    mammogram = get_object_or_404(Mammogram, pk=mammogram_id)

    # query metrics
    benign_count, malignant_count, total_count = get_mammogram_stats()
    metrics = ModelMetrics.objects.all()

    breast_density_category_mapping = {
        'category_a': "CATEGORY A",
        'category_b': "CATEGORY B",
        'category_c': "CATEGORY C",
        'category_d': "CATEGORY D"
    }

    breast_density_description_mapping = {
        'category_a': 'Breasts are almost entirely fatty',
        'category_b': 'There are scattered areas of dense tissue',
        'category_c': 'Breasts are heterogeneously dense',
        'category_d': 'Breasts are extremely dense'
    }

    breast_density_description = breast_density_description_mapping.get(mammogram.breast_density, 'Unknown')

    context = {
        'mammogram': mammogram,
        'prediction': mammogram.model_diagnosis,
        'describe_prediction': mammogram.descriptive_diagnosis,
        'birads_assessment': mammogram.birads_assessment,
        'probability_of_cancer': mammogram.probability_of_cancer,
        'breast_density': breast_density_description,
        'breast_density_category': breast_density_category_mapping.get(mammogram.breast_density, 'Unknown'),
        'benign_count': benign_count,
        'malignant_count': malignant_count,
        'total_count': total_count,
        'metrics': metrics,
        'confusion_matrix_data_url': reverse('confusion_matrix_data')
    }

    return render(request, 'predictions/results.html' , context)

def generate_report_view(request, mammogram_id):
    mammogram = get_object_or_404(Mammogram, pk=mammogram_id)
    patient = mammogram.patient

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{patient.first_name}{patient.last_name}_diagnosis report_{mammogram_id}.pdf"'

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CenteredHeading", fontSize=18, spaceAfter=10, alignment=1, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="SubHeading", fontSize=14, spaceAfter=6, fontName="Helvetica-Bold", underlineWidth=1, alignment=0))
    styles.add(ParagraphStyle(name="CustomBodyText", fontSize=12, leading=16, spaceAfter=10))
    styles.add(ParagraphStyle(name="TableHeader", fontSize=12, textColor=colors.white, backColor=HexColor("#FFEEF0"), alignment=1))
    styles.add(ParagraphStyle(name="Date", fontSize=12, textColor=colors.grey, alignment=TA_RIGHT))

    elements = []

    # add logo
    logo_path = os.path.join(settings.STATICFILES_DIRS[0], 'images', 'nina-logo.png')
    elements.append(Image(logo_path, width=100, height=50))
    elements.append(Spacer(1, 5))
    
    logo_description = "Nina Breast Cancer Detection System"
    elements.append(Paragraph(logo_description, ParagraphStyle(name="LogoDescription", fontSize=12, alignment=1, textColor=colors.grey)))
    elements.append(Spacer(1, 12))
    
    elements.append(Paragraph("Breast Cancer Diagnosis Report", styles['CenteredHeading']))
    elements.append(Paragraph(mammogram.uploaded_at.strftime('%d-%m-%Y'), styles['Date']))
    elements.append(Spacer(1, 20))

    # patient information
    elements.append(Paragraph("Patient Information", styles["SubHeading"]))
    patient_info_data = [
        ["FIRST NAME:", patient.first_name],
        ["LAST NAME:", patient.last_name],
        ["AGE:", str(patient.age)]
    ]
    patient_info_table = Table(patient_info_data, colWidths=[150, 300])
    patient_info_table.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(patient_info_table)
    elements.append(Spacer(1, 10))

    # findings and diagnosis
    elements.append(Paragraph("SUMMARY FINDINGS", styles["SubHeading"]))
    findings_text = f"""
    The mammogram was analyzed using a ResNet18 model for image-based classification 
    and a Random Forest Classifier for mass attributes. The model predicted the diagnosis as 
    <b>{mammogram.model_diagnosis}</b>.
    """
    elements.append(Paragraph(findings_text, styles["CustomBodyText"]))
    elements.append(Spacer(1, 10))

    # mammogram image
    elements.append(Paragraph("MAMMOGRAM IMAGE", styles["SubHeading"]))
    elements.append(Spacer(1, 5))
    mammogram_image_path = mammogram.image.path
    elements.append(Image(mammogram_image_path, width=80, height=80))
    elements.append(Spacer(1, 15))

    # mass attributes table
    elements.append(Paragraph("MASS ATTRIBUTES", styles["SubHeading"]))
    attributes_data = [
        ["Mass Shape", mammogram.mass_shape],
        ["Mass Margin", mammogram.mass_margin],
        ["Breast Density", mammogram.breast_density]
    ]
    attributes_table = Table(attributes_data, colWidths=[200, 300])
    attributes_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor("#FFEEF0")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(attributes_table)
    elements.append(Spacer(1, 15))

    # mass attributes prediction
    elements.append(Paragraph("Mass Attributes Prediction", styles["SubHeading"]))
    elements.append(Paragraph(f"""
    Based on mass attributes, the Random Forest Classifier predicted the diagnosis as 
    <b>{mammogram.descriptive_diagnosis}</b>. The patient has a breast density of 
    <b>{mammogram.breast_density}</b>.
    """, styles["CustomBodyText"]))
    elements.append(Spacer(1, 10))

    # BIRADS assessment
    elements.append(Paragraph("BIRADS Assessment", styles["SubHeading"]))
    elements.append(Paragraph(f"""
    The BIRADS model classifies the patient's cancer level as 
    <b>{mammogram.birads_assessment}</b> with a probability of 
    <b>{mammogram.probability_of_cancer}%</b>.
    """, styles["CustomBodyText"]))
    elements.append(Spacer(1, 10))

    # recommendation
    elements.append(Paragraph("Recommendations", styles["SubHeading"]))
    elements.append(Paragraph("""
    If the model's predictions align with the radiologist's assessment, 
    further consultation with a healthcare provider is recommended.
    """, styles["CustomBodyText"]))
    elements.append(Spacer(1, 20))

    footer_logo_path = os.path.join(settings.STATICFILES_DIRS[0], 'images', 'nina-logo.png')
    elements.append(Image(footer_logo_path, width=50, height=25))
    elements.append(Spacer(1, 5))

    # footer text
    footer_text = "Nina Breast Cancer Detection System | Contact: support@ninahealth.com"
    elements.append(Paragraph(footer_text, ParagraphStyle(name="Footer", fontSize=10, alignment=1, textColor=colors.grey)))

    doc.build(elements)

    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)

    return response

def generate_weekly_summary():
        today = now().date()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        # diagnosis during the week
        weekly_data = Mammogram.objects.filter(uploaded_at__range=[week_start, week_end])
        
        # benign and malignant count
        benign_cases = weekly_data.filter(model_diagnosis='Benign').count()
        malignant_cases = weekly_data.filter(model_diagnosis='Malignant').count()
        total_patients = weekly_data.count()

        # store summary
        summary, created = WeeklySummary.objects.get_or_create(
            week_start=week_start, week_end=week_end,
            defaults={
                'total_patients': total_patients, 
                'benign_cases': benign_cases, 
                'malignant_cases': malignant_cases
            }
        )

        return summary

def weekly_summary_view(request):
    weekly_summary = generate_weekly_summary()
    return render(request, 'predictions/weekly_summary.html', {'weekly_summary': weekly_summary})

def weekly_summary_report(request):
    summary = generate_weekly_summary()

    response = HttpResponse(content_type='application/pdf') 
    response['Content-Disposition'] = f'attachment; filename="weekly_summary_{summary.week_start}.pdf"'

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Title", fontSize=16, alignment=1, spaceAfter=12))
    styles.add(ParagraphStyle(name="TableHeader", fontSize=12, textColor=colors.white, backColor=colors.black, alignment=10))

    elements = []

    # header
    header_logo_path = os.path.join(settings.STATICFILES_DIRS[0], 'images', 'nina-logo.png')
    elements.append(Image(header_logo_path, width=100, height=50))
    elements.append(Spacer(1, 5))

    logo_description = "Nina Breast Cancer Detection System"
    elements.append(Paragraph(logo_description, ParagraphStyle(name="LogoDescription", fontSize=12, alignment=1, textColor=colors.grey)))
    elements.append(Spacer(1, 12))

    # title
    elements.append(Paragraph(f"Weekly Summary Report ({summary.week_start} - {summary.week_end})", styles['Title']))
    elements.append(Spacer(1, 12))

    # summary table
    data = [
        ["Total Patients", "Benign Cases", "Malignant Cases"],
        [summary.total_patients, summary.benign_cases, summary.malignant_cases]
    ]
    table = Table(data, colWidths=[150, 150, 150])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("Weekly Summary Report generated by Nina Breast Cancer Detection System", styles['Normal']))
    elements.append(Spacer(1, 12))

    # footer
    footer_logo_path = os.path.join(settings.STATICFILES_DIRS[0], 'images', 'nina-logo.png')
    elements.append(Image(footer_logo_path, width=50, height=25))
    elements.append(Spacer(1, 5))

    # footer text
    footer_text = "Nina Breast Cancer Detection System | Contact: support@ninahealth.com"
    elements.append(Paragraph(footer_text, ParagraphStyle(name="Footer", fontSize=10, alignment=1, textColor=colors.grey)))

def detailed_reports_view(request):
    detailed_data = Mammogram.objects.select_related("patient")
def reports_view(request):
    weekly_summary = generate_weekly_summary()
    return render(request, 'predictions/reports.html', {'weekly_summary': weekly_summary})