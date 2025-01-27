from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from .forms import MammogramForm
from .models import Mammogram
from .predictions import predict, get_mammogram_stats, calculate_metrics
import time
import os
from django.conf import settings


def upload_mammogram(request):
    image_id = request.GET.get('image_id')
    if request.method == 'POST':
        form = MammogramForm(request.POST, request.FILES)
        if form.is_valid():
            mammogram = form.save()
            # messages.success(request, 'Mammogram uploaded successfully.')
            return HttpResponseRedirect(reverse('process_mammogram', args=[mammogram.image_id]))
    else:
        if image_id:
            image_path = os.path.join(settings.MEDIA_ROOT, 'images', f'images/mammograms/{image_id}.jpg')
            if os.path.exists(image_path):
                with open(image_path, 'rb') as f:
                    form = MammogramForm({'image': f})
            else:
                form = MammogramForm()
        else:
            form = MammogramForm()
    return render(request, 'predictions/upload_image.html', {'form': form})

def processing_view(request, mammogram_id):
    mammogram = get_object_or_404(Mammogram, pk=mammogram_id)
    return render(request, 'predictions/process_image.html', {'mammogram_id': mammogram_id})

def predict_and_redirect_view(request, mammogram_id):
    mammogram = get_object_or_404(Mammogram, pk=mammogram_id)

    prediction_result = predict(mammogram.image.path)
    mammogram.model_diagnosis = prediction_result
    mammogram.save()

    return HttpResponseRedirect(reverse('results', args=[mammogram.image_id]))
    

def results_view(request, mammogram_id):
    mammogram = get_object_or_404(Mammogram, pk=mammogram_id)

    # query metrics
    benign_count, malignant_count, total_count = get_mammogram_stats()
    accuracy, precision, recall, f1_score, sensitivity, specificity = calculate_metrics()

    context = {
        'mammogram': mammogram,
        'prediction': mammogram.model_diagnosis,
        'benign_count': benign_count,
        'malignant_count': malignant_count,
        'total_count': total_count,
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1_score': f1_score,
        'sensitivity': sensitivity,
        'specificity': specificity
    }

    return render(request, 'predictions/results.html' , context)
