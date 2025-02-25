from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from .forms import MammogramForm
from .models import Mammogram, ModelMetrics
from .predictions import predict, get_mammogram_stats
from .descriptive_predictions import describe_predict
from django.conf import settings
import os

def upload_mammogram(request):
    image_id = request.GET.get('image_id')
    if request.method == 'POST':
        mammogram_form = MammogramForm(request.POST, request.FILES)
        if mammogram_form.is_valid():
            # patient_id = request.POST.get('patient_id')
            # patient, created = Patient.objects.get_or_create(
            #     patient_id=patient_id,
            #     defaults={'name': "Angela Chacha", 'age': 22}
            # )
            mammogram = mammogram_form.save(commit=False)
            # mammogram.patient = patient
            mammogram.save()
            return HttpResponseRedirect(reverse('predict_and_redirect', args=[mammogram.image_id]))
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
    return render(request, 'predictions/process_image.html', {'mammogram_id': mammogram_id})

def predict_and_redirect_view(request, mammogram_id):
    mammogram = get_object_or_404(Mammogram, pk=mammogram_id)

    # predictions based on the image
    prediction_result = predict(mammogram.image.path)
    mammogram.model_diagnosis = prediction_result

    # predictions based on mass attributes
    mass_margin = mammogram.mass_margin
    mass_shape = mammogram.mass_shape
    breast_density = mammogram.breast_density
    describe_prediction, birads_prediction = describe_predict(mass_margin, mass_shape, breast_density)
    mammogram.descriptive_diagnosis = describe_prediction
    mammogram.birads_assessment = birads_prediction


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
        'breast_density': breast_density_description,
        'breast_density_category': breast_density_category_mapping.get(mammogram.breast_density, 'Unknown'),
        'benign_count': benign_count,
        'malignant_count': malignant_count,
        'total_count': total_count,
        'metrics': metrics
    }

    return render(request, 'predictions/results.html' , context)
