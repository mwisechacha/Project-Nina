from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from .forms import MammogramForm
from .models import Mammogram
from .predictions import predict
import time


def upload_mammogram(request):
    if request.method == 'POST':
        form = MammogramForm(request.POST, request.FILES)
        if form.is_valid():
            mammogram = form.save()
            messages.success(request, 'Mammogram uploaded successfully.')
            return HttpResponseRedirect(reverse('process_mammogram', args=[mammogram.image_id]))
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

    return render(request, 'predictions/results.html' , {'mammogram': mammogram,
                                                         'prediction': mammogram.model_diagnosis})