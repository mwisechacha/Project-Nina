from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from .forms import MammogramForm, ModelMetricsForm
from .models import Mammogram
from .predictions import predict, get_mammogram_stats
from .descriptive_predictions import describe_predict
import time
import os
from django.conf import settings


def upload_mammogram(request):
    image_id = request.GET.get('image_id')
    if request.method == 'POST':
        mammogram_form = MammogramForm(request.POST, request.FILES)
        metrics_form = ModelMetricsForm(request.POST)
        if mammogram_form.is_valid() and metrics_form.is_valid():
            mammogram = mammogram_form.save()
            metrics = metrics_form.save(commit=False)
            metrics.mammogram = mammogram
            metrics.save()
            return HttpResponseRedirect(reverse('process_mammogram', args=[mammogram.image_id]))
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
        metrics_form = ModelMetricsForm()
    return render(request, 'predictions/upload_image.html', {'mammogram_form': mammogram_form,
                                                             'metrics_form': metrics_form})

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
    describe_prediction = describe_predict(mass_margin, mass_shape, breast_density)
    mammogram.descriptive_diagnosis = describe_prediction

    mammogram.save()
    print("Prediction saved")

    return HttpResponseRedirect(reverse('results', args=[mammogram.image_id]))
    

def results_view(request, mammogram_id):
    mammogram = get_object_or_404(Mammogram, pk=mammogram_id)

    # query metrics
    benign_count, malignant_count, total_count = get_mammogram_stats()

    context = {
        'mammogram': mammogram,
        'prediction': mammogram.model_diagnosis,
        'describe_prediction': mammogram.descriptive_diagnosis,
        'benign_count': benign_count,
        'malignant_count': malignant_count,
        'total_count': total_count,
        'metrics': mammogram.metrics.all()
    }

    return render(request, 'predictions/results.html' , context)
