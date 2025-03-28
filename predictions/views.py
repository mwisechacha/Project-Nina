from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils.timezone import now, timedelta, make_aware, localtime
from django.utils import timezone
from django.urls import reverse
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.platypus import PageTemplate, BaseDocTemplate, Frame, Paragraph
from statistics import mean
from .forms import MammogramForm, DisapproveForm
from .models import Mammogram, ModelMetrics, Patient, WeeklySummary, Radiologist, DisapprovedMammogram
from .predictions import predict, get_mammogram_stats
from .descriptive_predictions import describe_predict
from .utils import get_conf_matrix_data
from io import BytesIO
import os

def upload_mammogram(request):
    image_id = request.GET.get('image_id')

    search_query = request.GET.get('search', '').strip()
    selected_patient = None
    patients = []

    if search_query:
        patients = Patient.objects.filter(patient_id=search_query)
        if patients.exists():
            selected_patient = patients.first()
        else:
            print("No patient found with the given patient_id")
    
    if request.method == 'POST':
        mammogram_form = MammogramForm(request.POST, request.FILES)
        
        selected_patient_id = request.POST.get('selected_patient_id')
        if selected_patient_id:
            patient = get_object_or_404(Patient, pk=selected_patient_id)
        else:
            first_name = request.POST.get('patient_first_name', '').strip()
            last_name = request.POST.get('patient_last_name', '').strip()
            date_of_birth = request.POST.get('patient_date_of_birth', '').strip()
            patient, created = Patient.objects.get_or_create(
                first_name=first_name, last_name=last_name, date_of_birth=date_of_birth
            )

        try:
            radiologist = Radiologist.objects.get(user=request.user)
        except ObjectDoesNotExist:
            radiologist = Radiologist.objects.create(user=request.user)

        # validate image
        image = request.FILES.get('image')
        if image:
            valid_extensions = ['.png', '.jpg', '.jpeg']   
            ext = os.path.splitext(image.name)[1].lower()
            if ext not in valid_extensions:
                messages.error(request, 'Invalid image format. Only PNG, JPG, and JPEG are allowed.')
                return render(request, 'predictions/upload_image.html', {
                    'mammogram_form': mammogram_form,
                    'patients': patients,
                    'selected_patient': selected_patient,
                    'search_query': search_query
                })

        if mammogram_form.is_valid():  
            mammogram = mammogram_form.save(commit=False)
            mammogram.patient = patient
            mammogram.radiologist = radiologist
            mammogram.uploaded_at = timezone.now()
            mammogram.save()
            
            return HttpResponseRedirect(reverse('process_mammogram', args=[mammogram.image_id]))
        
        else:
            messages.error(request, "Please enter correct date of birth.")

    if image_id:
        image_path = os.path.join(settings.MEDIA_ROOT, 'images', f'images/mammograms/{image_id}.jpg')
        if os.path.exists(image_path):
            with open(image_path, 'rb') as f:
                mammogram_form = MammogramForm({'image': f})
        mammogram_form = MammogramForm()
    else:
        mammogram_form = MammogramForm()

    return render(request, 'predictions/upload_image.html', {
        'mammogram_form': mammogram_form,
        'patients': patients,
        'selected_patient': selected_patient,
        'search_query': search_query,
    })

def processing_view(request, mammogram_id):
    mammogram = get_object_or_404(Mammogram, pk=mammogram_id)
    results_url = reverse('predict_and_redirect', args=[mammogram.image_id])
    return render(request, 'predictions/process_image.html', {'mammogram_id': mammogram_id, 'results_url': results_url})

def predict_and_redirect_view(request, mammogram_id):
    mammogram = get_object_or_404(Mammogram, pk=mammogram_id)

    # predictions based on the image
    prediction_result = predict(mammogram.image.path)
    mammogram.model_diagnosis = prediction_result

    # predictions based on mass attributes and image
    mass_margin = mammogram.mass_margin
    mass_shape = mammogram.mass_shape
    breast_density = mammogram.breast_density
    image_path = mammogram.image.path


    describe_prediction, birads_prediction, probability_of_cancer, recommendation = describe_predict(
        mass_margin, mass_shape, breast_density, image_path
        )
    
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
    if request.method == 'POST':
        if 'approve' in request.POST:
            if mammogram.approved:
                messages.error(request, 'Diagnosis has already been approved.')
                return HttpResponseRedirect(reverse('results', args=[mammogram.image_id]))
            
            mammogram.approved = True
            mammogram.save()
            messages.success(request, 'Hurray! Diagnosis has been approved. Check the diagnosis report for more information.')
            return HttpResponseRedirect(reverse('generate_report', args=[mammogram.image_id]))
        else:
            if DisapprovedMammogram.objects.filter(mammogram=mammogram).exists():
                messages.error(request, 'Diagnosis has already been disapproved.')
                return HttpResponseRedirect(reverse('results', args=[mammogram.image_id]))
            
            form = DisapproveForm(request.POST)
            if form.is_valid():
                pathology_actual = form.cleaned_data['pathology_actual']
                descriptive_actual = form.cleaned_data['descriptive_actual']
                birads_actual = form.cleaned_data['birads_actual']
                comments = form.cleaned_data['comments']

                disapproved_record = DisapprovedMammogram.objects.create(
                    mammogram=mammogram,
                    pathology_actual=pathology_actual,
                    descriptive_actual=descriptive_actual,
                    birads_actual=birads_actual,
                    comments=comments
                )

                mammogram.approved = False
                mammogram.save()
                messages.success(request, 'Diagnosis Rejected. Please try uploading another image.')
                return HttpResponseRedirect(reverse('results', args=[mammogram.image_id]))
    else:
        form = DisapproveForm(initial={
            'pathology_predicted': mammogram.model_diagnosis,
            'descriptive_prediction': mammogram.descriptive_diagnosis,
            'birads_prediction': mammogram.birads_assessment,
    })

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
        'confusion_matrix_data_url': reverse('confusion_matrix_data'),
        'form': form
    }

    return render(request, 'predictions/results.html' , context)

def approve_results_view(request, mammogram_id):
    mammogram = get_object_or_404(Mammogram, pk=mammogram_id)
    mammogram.approved = True
    mammogram.save()
    return HttpResponseRedirect(reverse('generate_report', args=[mammogram.image_id]))

def generate_report_view(request, mammogram_id):
    mammogram = get_object_or_404(Mammogram, pk=mammogram_id)
    patient = mammogram.patient

    # get recommendation
    _, _, _, recommendation = describe_predict(mammogram.mass_margin, mammogram.mass_shape, mammogram.breast_density, mammogram.image.path)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{patient.first_name}{patient.last_name}_diagnosis report_{mammogram_id}.pdf"'

    buffer = BytesIO()

    def add_page_number(canvas, doc):
            page_number_text = f"Page {doc.page}"
            canvas.setFont("Helvetica", 10)
            canvas.drawRightString(200 * mm, 10 * mm, page_number_text)

    doc = SimpleDocTemplate(buffer, pagesize=letter)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CenteredHeading", fontSize=18, spaceAfter=10, alignment=1, fontName="Helvetica-Bold", textColor=HexColor("#94126A")))
    styles.add(ParagraphStyle(name="SubHeading", fontSize=14, spaceAfter=6, fontName="Helvetica-Bold", textColor=HexColor("#94126A"), underlineWidth=1, alignment=0))
    styles.add(ParagraphStyle(name="CustomBodyText", fontSize=12, leading=16, spaceAfter=10))
    styles.add(ParagraphStyle(name="TableHeader", fontSize=12, textColor=colors.white, backColor=HexColor("#94126A"), alignment=1))
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
        ["AGE:", str(patient.age())]
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
        ["ATTRIBUTE", "VALUE"],
        ["Mass Shape", mammogram.mass_shape],
        ["Mass Margin", mammogram.mass_margin],
        ["Breast Density", mammogram.breast_density]
    ]
    attributes_table = Table(attributes_data, colWidths=[80, 300])
    attributes_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor("#94126A")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), HexColor("#FFEEF0")),
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
    elements.append(Spacer(1, 30))

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
    elements.append(Paragraph(recommendation, styles["CustomBodyText"]))
    elements.append(Spacer(1, 20))

    footer_logo_path = os.path.join(settings.STATICFILES_DIRS[0], 'images', 'nina-logo.png')
    elements.append(Image(footer_logo_path, width=50, height=25))
    elements.append(Spacer(1, 5))

    # footer text
    footer_text = '<font color="#94126A"><b>Nina Breast Cancer Detection System</b></font>'
    elements.append(Paragraph(footer_text, ParagraphStyle(name="Footer", fontSize=10, alignment=1, textColor=colors.grey)))

    doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)

    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)

    return response

def generate_weekly_summary(radiologist):
        today = now().date()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)

        week_start = make_aware(datetime.combine(week_start, datetime.min.time()))
        week_end = make_aware(datetime.combine(week_end, datetime.max.time()))

        week_start_local = localtime(week_start)
        week_end_local = localtime(week_end)

        # Diagnosis during the week
        weekly_data = Mammogram.objects.filter(
            uploaded_at__range=[week_start_local, week_end_local],
            radiologist=radiologist
        )

        # Benign and malignant count
        benign_cases = weekly_data.filter(model_diagnosis='Benign').count()
        malignant_cases = weekly_data.filter(model_diagnosis='Malignant').count()
        total_patients = weekly_data.count()

        # Daily breakdown
        daily_breakdown = []
        for i in range(7):
            day = week_start + timedelta(days=i)
            day_start = localtime(day).replace(hour=0, minute=0, second=0)
            day_end = localtime(day).replace(hour=23, minute=59, second=59)
            day_data = weekly_data.filter(uploaded_at__range=[day_start, day_end])
            
            benign_count = day_data.filter(model_diagnosis='Benign').count()
            malignant_count = day_data.filter(model_diagnosis='Malignant').count()
            total_count = day_data.count()

            daily_breakdown.append({
                'day': day.date(),
                'benign_cases': benign_count,
                'malignant_cases': malignant_count,
                'total_patients': total_count
            })

        # previous week data
        previous_week_start = week_start - timedelta(days=7)
        previous_week_end = week_end - timedelta(days=7)
        previous_week_data = Mammogram.objects.filter(uploaded_at__range=[previous_week_start, previous_week_end], radiologist=radiologist)
        previous_week_summary = {
            'benign_cases': previous_week_data.filter(model_diagnosis='Benign').count(),
            'malignant_cases': previous_week_data.filter(model_diagnosis='Malignant').count(),
            'total_patients': previous_week_data.count()
        }

        # additional metrics
        birth_dates = weekly_data.values_list('patient__date_of_birth', flat=True)

        ages = []
        current_date = now().date()

        for birth_date in birth_dates:
            if birth_date:
                age = current_date.year - birth_date.year
                if (birth_date.month, birth_date.day) > (current_date.month, current_date.day):
                    age -= 1
                ages.append(age)

        average_age = mean(ages) if ages else None
        average_age = round(average_age, 2) if average_age else None
        breast_density_distribution = weekly_data.values('breast_density').annotate(count=Count('breast_density'))

        # store summary
        summary, created = WeeklySummary.objects.update_or_create(
            week_start=week_start, week_end=week_end, radiologist=radiologist,
            defaults={
                'total_patients': total_patients, 
                'benign_cases': benign_cases, 
                'malignant_cases': malignant_cases
            }
        )

        return summary, daily_breakdown, previous_week_summary, average_age, breast_density_distribution

@login_required
def weekly_summary_view(request):
    try:
        radiologist = Radiologist.objects.get(user=request.user)
    except Radiologist.DoesNotExist:
        radiologist = None

    if radiologist:
        weekly_summary, daily_breakdown, previous_week, average_age, breast_density_distribution = generate_weekly_summary(radiologist)
        context = {
            'weekly_summary': weekly_summary,
            'total_patients': weekly_summary.total_patients,
            'benign_cases': weekly_summary.benign_cases,
            'malignant_cases': weekly_summary.malignant_cases,
            'start_week': weekly_summary.week_start,
            'end_week': weekly_summary.week_end,
            'daily_breakdown': daily_breakdown,
            'previous_week': previous_week,
            'average_age': average_age,
            'breast_density_distribution': breast_density_distribution
        }
    else:
        context = {
            'weekly_summary': None,
            'total_patients': 0,
            'benign_cases': 0,
            'malignant_cases': 0,
            'start_week': None,
            'end_week': None,
            'daily_breakdown': [],
            'previous_week': {},
            'average_age': None,
            'breast_density_distribution': []
        }

    return render(request, 'predictions/weekly_summary.html', context)

def weekly_summary_report(request):
    try:
        radiologist = Radiologist.objects.get(user=request.user)
    except Radiologist.DoesNotExist:
        radiologist = None

    if radiologist:
        summary, daily_breakdown, previous_week, _, _ = generate_weekly_summary(radiologist)

        response = HttpResponse(content_type='application/pdf') 
        response['Content-Disposition'] = f'attachment; filename="weekly_summary_{summary.week_start}.pdf"'

        buffer = BytesIO()

        def add_page_number(canvas, doc):
            page_number_text = f"Page {doc.page}"
            canvas.setFont("Helvetica", 10)
            canvas.drawRightString(200 * mm, 10 * mm, page_number_text)

        doc = SimpleDocTemplate(buffer, pagesize=letter)

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name="CustomTitle", fontSize=16, alignment=1, spaceAfter=12))
        styles.add(ParagraphStyle(name="CustomTableHeader", fontSize=12, textColor=colors.white, backColor=colors.black, alignment=10))

        elements = []

        # header
        header_logo_path = os.path.join(settings.STATICFILES_DIRS[0], 'images', 'nina-logo.png')
        elements.append(Image(header_logo_path, width=100, height=50))
        elements.append(Spacer(1, 5))

        logo_description = "Nina Breast Cancer Detection System"
        elements.append(Paragraph(logo_description, ParagraphStyle(name="LogoDescription", fontSize=12, alignment=1, textColor=colors.grey)))
        elements.append(Spacer(1, 12))

        # title
        elements.append(Paragraph(f"""<font color="#94126A"><b> Weekly Summary</b></font><br/> 
                                  <font color="black">({summary.week_start} - {summary.week_end})</font>""", 
                                  styles['Title']))
        elements.append(Spacer(1, 12))

        # summary table
        data = [
            ["Total Patients", "Benign Cases", "Malignant Cases"],
            [summary.total_patients, summary.benign_cases, summary.malignant_cases]
        ]
        table1 = Table(data, colWidths=[150, 150, 150])
        table1.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor("#94126A")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BACKGROUND', (0, 1), (-1, -1), HexColor("#FFEEF0")),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))

        for i in range(1, len(data)):
            if i % 2 == 0:
                table1.setStyle(TableStyle([
                    ('BACKGROUND', (0, i), (-1, i), HexColor("#FFEEF0")),  
                ]))
            else:
                table1.setStyle(TableStyle([
                    ('BACKGROUND', (0, i), (-1, i), HexColor("#FFEEF0")),
                ]))

        elements.append(table1)
        elements.append(Spacer(1, 12))

        # daily breakdown
        elements.append(Paragraph("""<font color="#94126A"><b> Daily Breakdown</b></font>""", styles['CustomTitle']))
        elements.append(Spacer(1, 12))

        daily_breakdown_data = [
            ["Day", "Total Patients", "Benign Cases", "Malignant Cases"]
        ] + [
            [entry['day'], entry['total_patients'], entry['benign_cases'], entry['malignant_cases']] for entry in daily_breakdown
        ]

        table2 = Table(daily_breakdown_data, colWidths=[150, 150, 150, 150])
        table2.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor("#94126A")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BACKGROUND', (0, 1), (-1, -1), HexColor("#FFEEF0")),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))

        for i in range(1, len(data)):
            if i % 2 == 0:
                table2.setStyle(TableStyle([
                    ('BACKGROUND', (0, i), (-1, i), HexColor("#FFEEF0")),  
                ]))
            else:
                table2.setStyle(TableStyle([
                    ('BACKGROUND', (0, i), (-1, i), HexColor("#FFEEF0")),
                ]))

        elements.append(table2)
        elements.append(Spacer(1, 12))

        # previous week summary
        elements.append(Paragraph("""<font color="#94126A"><b> Previous Week Summary</b></font> """, styles['CustomTitle']))
        elements.append(Spacer(1, 12))

        previous_week_data = [
            ["Metrics", "Previous Week", "Current Week", "Change"]
            ] + [
            ["Total Patients", previous_week['total_patients'], summary.total_patients, summary.total_patients - previous_week['total_patients']],
            ["Benign Cases", previous_week['benign_cases'], summary.benign_cases, summary.benign_cases - previous_week['benign_cases']],
            ["Malignant Cases", previous_week['malignant_cases'], summary.malignant_cases, summary.malignant_cases - previous_week['malignant_cases']]
            ]
        
        table3 = Table(previous_week_data, colWidths=[150, 150, 150])
        table3.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor("#94126A")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BACKGROUND', (0, 1), (-1, -1), HexColor("#FFEEF0")),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))

        for i in range(1, len(data)):
            if i % 2 == 0:
                table2.setStyle(TableStyle([
                    ('BACKGROUND', (0, i), (-1, i), HexColor("#FFEEF0")),  
                ]))
            else:
                table2.setStyle(TableStyle([
                    ('BACKGROUND', (0, i), (-1, i), HexColor("#FFEEF0")),
                ]))

        elements.append(table3)
        elements.append(Spacer(1, 5))

        # footer
        footer_logo_path = os.path.join(settings.STATICFILES_DIRS[0], 'images', 'nina-logo.png')
        elements.append(Image(footer_logo_path, width=50, height=25))
        elements.append(Spacer(1, 5))

        # footer text
        footer_text = '<font color="#94126A"><b>Nina Breast Cancer Detection System</b></font>'
        elements.append(Paragraph(footer_text, ParagraphStyle(name="Footer", fontSize=10, alignment=1, textColor=colors.grey)))

        doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)

        pdf = buffer.getvalue()
        buffer.close()
        response.write(pdf)

        return response
    else:
        summary = None
        return render(request, 'predictions/weekly_summary.html', {'weekly_summary': summary})

@login_required
def benign_reports(request):
    try:
        radiologist = Radiologist.objects.get(user=request.user)
    except Radiologist.DoesNotExist:
        radiologist = None

    if radiologist:
        benign_data = Mammogram.objects.filter(
            radiologist=radiologist,
            model_diagnosis='Benign'
        ).select_related("patient", "radiologist").order_by('-uploaded_at')
    else:
        benign_data = Mammogram.objects.none()

    return render(request, 'predictions/benign_reports.html', {'benign_data': benign_data})

@login_required
def malignant_reports(request):
    try:
        radiologist = Radiologist.objects.get(user=request.user)
    except Radiologist.DoesNotExist:
        radiologist = None

    if radiologist:
        malignant_data = Mammogram.objects.filter(
            radiologist=radiologist,
            model_diagnosis='Malignant'
        ).select_related("patient", "radiologist").order_by('-uploaded_at')
    else:
        malignant_data = Mammogram.objects.none()

    return render(request, 'predictions/malignant_reports.html', {'malignant_data': malignant_data})

@login_required
def detailed_reports_view(request):
    try:
        radiologist = Radiologist.objects.get(user=request.user)
    except Radiologist.DoesNotExist:
        radiologist = None

    filter_option = request.GET.get('filter', 'all')

    if radiologist:
        end_date = timezone.now()
        start_date = end_date - timedelta(days=7)

        detailed_data = Mammogram.objects.filter(
            radiologist=radiologist,
            uploaded_at__range=[start_date, end_date]
            ).select_related("patient", "radiologist").order_by('-uploaded_at')
        
        # apply filters
        if filter_option == 'benign':
            detailed_data = detailed_data.filter(model_diagnosis='Benign')
        elif filter_option == 'malignant':
            detailed_data = detailed_data.filter(model_diagnosis='Malignant')
        elif filter_option == 'approved':
            detailed_data = detailed_data.filter(approved=True)
        elif filter_option == 'disapproved':
            detailed_data = detailed_data.filter(approved=False)
    else:
        detailed_data = Mammogram.objects.none()

    return render(request, 'predictions/detailed_report.html', {
        'detailed_data': detailed_data,
        'filter': filter_option,
        'start_date': start_date,
        'end_date': end_date})

def generate_detailed_report(request):
    try:
        radiologist = Radiologist.objects.get(user=request.user)
    except Radiologist.DoesNotExist:
        radiologist = None

    if radiologist:
        end_date = timezone.now()
        start_date = end_date - timedelta(days=7)

        filter_option = request.GET.get('filter', 'all')

        mammograms = Mammogram.objects.filter(
            radiologist=radiologist,
            uploaded_at__range=[start_date, end_date]
            ).select_related("patient", "radiologist").order_by('-uploaded_at')
        
        if filter_option == 'benign':
            mammograms = mammograms.filter(model_diagnosis='Benign')
        elif filter_option == 'malignant':
            mammograms = mammograms.filter(model_diagnosis='Malignant')
        elif filter_option == 'approved':
            mammograms = mammograms.filter(approved=True)
        elif filter_option == 'disapproved':
            mammograms = mammograms.filter(approved=False)

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="detailed_report_{filter_option}_{start_date}.pdf"'

        buffer = BytesIO()

        def add_page_number(canvas, doc):
            page_number_text = f"Page {doc.page}"
            canvas.setFont("Helvetica", 10)
            canvas.drawRightString(200 * mm, 10 * mm, page_number_text)

        doc = SimpleDocTemplate(buffer, pagesize=letter)

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name="CenteredHeading", fontSize=18, alignment=1, fontName="Helvetica-Bold"))
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
        
        elements.append(Paragraph(
            f"""<font color="#94126A"><b>Breast Cancer Report {filter_option.capitalize()} cases</b></font><br/>
            <font color="black">for the period between ({start_date.strftime('%Y-%m-%d')} and {end_date.strftime('%Y-%m-%d')})</font>""",
            styles['Title']
        ))
        elements.append(Spacer(1, 20))

        data = [
            ["S/N", "PName", "Age", "Radiologist", "Analysis Date", "MD", "Descr", "BI-RADS", "PB", "APR"]
        ]

        for index, mammogram in enumerate(mammograms, start=1):
            radiologist_name = f"Dr. {mammogram.radiologist.user.first_name} {mammogram.radiologist.user.last_name}" if mammogram.radiologist else "N/A"
            data.append([
                Paragraph(str(index), styles["CustomBodyText"]),
                Paragraph(f"{mammogram.patient.first_name or 'N/A'} {mammogram.patient.last_name or 'N/A'}", styles["CustomBodyText"]),
                Paragraph(str(mammogram.patient.age() or "N/A"), styles["CustomBodyText"]),
                Paragraph(radiologist_name, styles["CustomBodyText"]),
                Paragraph(mammogram.uploaded_at.strftime("%Y-%m-%d") if mammogram.uploaded_at else "N/A", styles["CustomBodyText"]),
                Paragraph(mammogram.model_diagnosis.lower() or "N/A", styles["CustomBodyText"]),
                Paragraph(mammogram.descriptive_diagnosis.lower() or "N/A", styles["CustomBodyText"]),
                Paragraph(mammogram.birads_assessment or "N/A", styles["CustomBodyText"]),
                Paragraph(f"{mammogram.probability_of_cancer}%" if mammogram.probability_of_cancer is not None else "N/A", styles["CustomBodyText"]),
                Paragraph("Yes" if mammogram.approved else "No", styles["CustomBodyText"])
            ])
            
        table = Table(data, colWidths=[30, 80, 40, 80, 80, 70, 65, 90, 40, 40]) 
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor("#94126A")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),  
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('BACKGROUND', (0, 1), (-1, 1), HexColor("#FFEEF0")),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), 
        ]))

        for i in range(1, len(data)):
            if i % 2 == 0:
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, i), (-1, i), HexColor("#FFEEF0")),  
                ]))
            else:
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, i), (-1, i), HexColor("#FFEEF0")),
                ]))

        elements.append(table)
        elements.append(Spacer(1, 15))

        footer_logo_path = os.path.join(settings.STATICFILES_DIRS[0], 'images', 'nina-logo.png')
        elements.append(Image(footer_logo_path, width=50, height=25))
        elements.append(Spacer(1, 5))

        # footer text
        footer_text = '<font color="#94126A"><b>Nina Breast Cancer Detection System</b></font>'
        elements.append(Paragraph(footer_text, ParagraphStyle(name="Footer", fontSize=10, alignment=1, textColor=colors.grey)))

        doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)

        pdf = buffer.getvalue()
        buffer.close()
        response.write(pdf)

        return response
    else:
        mammograms = Mammogram.objects.none()
        start_date = None
        end_date = None

        return render(request, 'predictions/detailed_report.html', {'mammograms': mammograms})


@login_required
def exceptional_reports_view(request):
    try:
        radiologist = Radiologist.objects.get(user=request.user)
    except Radiologist.DoesNotExist:
        radiologist = None

    if radiologist:
        end_date = timezone.now()
        start_date = end_date - timedelta(days=7)
        disapproved_mammograms = DisapprovedMammogram.objects.filter(
            mammogram__radiologist=radiologist,
            mammogram__uploaded_at__range=[start_date, end_date]
            ).select_related("mammogram__patient", "mammogram__radiologist").order_by('-mammogram__uploaded_at')
    else:
        disapproved_mammograms = DisapprovedMammogram.objects.none()
        start_date = None
        end_date = None

    return render(request, 'predictions/exceptional_reports.html', {
        'disapproved_mammograms': disapproved_mammograms,
        'start_date': start_date,
        'end_date': end_date})

def generate_exceptional_report(request):
    try:
        radiologist = Radiologist.objects.get(user=request.user)
    except Radiologist.DoesNotExist:
        radiologist = None

    if radiologist:
        end_date = timezone.now()
        start_date = end_date - timedelta(days=7)
        disapproved_mammograms = DisapprovedMammogram.objects.filter(
            mammogram__radiologist=radiologist,
            mammogram__uploaded_at__range=[start_date, end_date]
            ).select_related("mammogram__patient", "mammogram__radiologist").order_by('-mammogram__uploaded_at')
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="exceptional_report_{start_date}.pdf"'

        buffer = BytesIO()

        # add page number
        def add_page_number(canvas, doc):
            page_number_text = f"Page {doc.page}"
            canvas.setFont("Helvetica", 10)
            canvas.drawRightString(200 * mm, 10 * mm, page_number_text)

        doc = SimpleDocTemplate(buffer, pagesize=letter)

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name="CenteredHeading", fontSize=18, spaceAfter=10, alignment=1, fontName="Helvetica-Bold"))
        styles.add(ParagraphStyle(name="SubHeading", fontSize=14, spaceAfter=6, fontName="Helvetica-Bold", underlineWidth=1, alignment=0))
        styles.add(ParagraphStyle(name="CustomBodyText", fontSize=10, leading=12, spaceAfter=10)) 
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

        elements.append(Paragraph(f"""<font color="#94126A"><b>Breast Cancer Report for Disapproved cases</b></font><br/>
                                  <font color="black"> for the period between ({start_date.strftime('%Y-%m-%d')} and {end_date.strftime('%Y-%m-%d')})</font>""", 
                                  styles['Title']))
        elements.append(Spacer(1, 20))

        # fetch data
        data = [
            ["S/N", "PatientName", "Age", "Radiologist", "ActualDiagnosis", "ActualDescr", "ActualBIRADS", "UploadedAt"]
        ]

        for index, entry in enumerate(disapproved_mammograms, start=1):
            radiologist_name = f"Dr. {entry.mammogram.radiologist.user.first_name} {entry.mammogram.radiologist.user.last_name}" if entry.mammogram.radiologist else "N/A"
            data.append([
                Paragraph(str(index), styles["CustomBodyText"]),
                Paragraph(f"{entry.mammogram.patient.first_name} {entry.mammogram.patient.last_name}", styles["CustomBodyText"]),
                Paragraph(str(entry.mammogram.patient.age()), styles["CustomBodyText"]),
                Paragraph(radiologist_name, styles["CustomBodyText"]),
                Paragraph(entry.pathology_actual, styles["CustomBodyText"]),
                Paragraph(entry.descriptive_actual, styles["CustomBodyText"]),
                Paragraph(entry.birads_actual, styles["CustomBodyText"]),
                Paragraph(entry.mammogram.uploaded_at.strftime("%Y-%m-%d"), styles["CustomBodyText"])
            ])

        table = Table(data, colWidths=[40, 85, 35, 80, 85, 90, 80, 80])  
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor("#94126A")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10), 
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('BACKGROUND', (0, 1), (-1, -1), HexColor("#FFEEF0")),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP') 
        ]))

        for i in range(1, len(data)):
            if i % 2 == 0:
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, i), (-1, i), HexColor("#FFEEF0")),  
                ]))
            else:
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, i), (-1, i), HexColor("#FFEEF0")),
                ]))

        elements.append(table)
        elements.append(Spacer(1, 15))

        footer_logo_path = os.path.join(settings.STATICFILES_DIRS[0], 'images', 'nina-logo.png')
        elements.append(Image(footer_logo_path, width=50, height=25))
        elements.append(Spacer(1, 5))

        # footer text
        footer_text = '<font color="#94126A"><b>Nina Breast Cancer Detection System</b></font>'
        elements.append(Paragraph(footer_text, ParagraphStyle(name="Footer", fontSize=10, alignment=1, textColor=colors.grey)))

        doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)
        
        pdf = buffer.getvalue()
        buffer.close()
        response.write(pdf)

        return response
    else:
        disapproved_mammograms = DisapprovedMammogram.objects.none()
        return render(request, 'predictions/exceptional_reports.html', {'disapproved_mammograms': disapproved_mammograms})

def reports_view(request):
    try:
        radiologist = Radiologist.objects.get(user=request.user)
    except Radiologist.DoesNotExist:
        radiologist = None

    if radiologist:
        weekly_summary, daily_breakdown, previous_week, average_age, breast_density_distribution = generate_weekly_summary(radiologist)
        detailed_data = Mammogram.objects.filter(radiologist=radiologist).select_related("patient", "radiologist").order_by('-uploaded_at')
        context = {
            'weekly_summary': weekly_summary,
            'total_patients': weekly_summary.total_patients,
            'benign_cases': weekly_summary.benign_cases,
            'malignant_cases': weekly_summary.malignant_cases,
            'start_week': weekly_summary.week_start,
            'end_week': weekly_summary.week_end,
            'daily_breakdown': daily_breakdown,
            'previous_week': previous_week,
            'average_age': average_age,
            'breast_density_distribution': breast_density_distribution,
            'detailed_data': detailed_data
        }
    else:
        context = {
            'weekly_summary': None,
            'total_patients': 0,
            'benign_cases': 0,
            'malignant_cases': 0,
            'start_week': None,
            'end_week': None,
            'daily_breakdown': [],
            'previous_week': {},
            'average_age': None,
            'breast_density_distribution': [],
            'detailed_data': []
        }

    return render(request, 'predictions/reports.html', context)