from io import BytesIO
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.template.loader import render_to_string
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from .forms import MammogramForm
from .models import Mammogram, ModelMetrics, Patient
from .predictions import predict, get_mammogram_stats
from .descriptive_predictions import describe_predict
from django.conf import settings
import os

def upload_mammogram(request):
    image_id = request.GET.get('image_id')
    if request.method == 'POST':
        mammogram_form = MammogramForm(request.POST, request.FILES)
        if mammogram_form.is_valid():
            patient_id = request.POST.get('patient_id')
            patient, created = Patient.objects.get_or_create(
                defaults={'name': "Angela Chacha", 'age': 22}
            )
            mammogram = mammogram_form.save(commit=False)
            mammogram.patient = patient
            mammogram.save()
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
        'metrics': metrics
    }

    return render(request, 'predictions/results.html' , context)

def generate_report_view(request, mammogram_id):
    mammogram = get_object_or_404(Mammogram, pk=mammogram_id)
    context = {
        'mammogram': mammogram,
        'prediction': mammogram.model_diagnosis,
        'describe_prediction': mammogram.descriptive_diagnosis,
        'birads_assessment': mammogram.birads_assessment,
        'breast_density': mammogram.breast_density,
        'breast_density_category': mammogram.breast_density,
    }

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="report_{mammogram_id}.pdf"'

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)

    styles = getSampleStyleSheet()
    styles['Heading1'].fontSize = 18
    styles['Heading1'].leading = 22
    styles['Heading1'].spaceAfter = 10
    styles['Heading1'].alignment = 1
    
    styles.add(ParagraphStyle(name='CustomHeading2', fontSize=14, leading=18, spaceAfter=10))
    styles.add(ParagraphStyle(name='CustomBodyText', fontSize=12, leading=14))

    # register font
    # font_path = os.path.join(settings.STATICFILES_DIRS[0], 'fonts', 'OpenSans-Regular.ttf')
    # pdfmetrics.registerFont(TTFont('OpenSans', font_path))

    elements = []

    # add logo
    logo_path = os.path.join(settings.STATICFILES_DIRS[0], 'images', 'nina-logo.png')
    elements.append(Image(logo_path, width=100, height=50))
    elements.append(Spacer(1, 12))


    elements.append(Paragraph(f"Diagnosis Report for {Patient.name}", styles['Heading1']))
    elements.append(Spacer(1, 12))

    # add mammogram image
    mammogram_image_path = mammogram.image.path
    elements.append(Image(mammogram_image_path, width=400, height=400))

    data = [
        ['Field', 'Value'],
        ['Pathology', mammogram.model_diagnosis],
        ['Birads Assessment', mammogram.birads_assessment],
        ['Breast Density', mammogram.breast_density],
        ['Mass Shape', mammogram.mass_shape],
        ['Mass Margin', mammogram.mass_margin]
    ]

    table = Table(data, colWidths=[150, 300])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor("#FFEEF0")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        # ('FONTNAME', (0, 0), (-1, 0), 'OpenSans'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 12))
    
    doc.build(elements)

    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)

    return response