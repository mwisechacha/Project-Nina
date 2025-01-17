from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from .forms import MammogramForm
from .models import Mammogram


def upload_mammogram(request):
    if request.method == 'POST':
        form = MammogramForm(request.POST, request.FILES)
        # if form.is_valid():
        #     mammogram = form.save()
        #     return HttpResponseRedirect(reverse('process_mammogram', args=[mammogram.id]))
    else:
        form = MammogramForm()
    return render(request, 'predictions/upload_image.html', {'form': form})

def processing_view(request):
    # mammogram = Mammogram.objects.get(pk=mammogram_id)

    # process the mammogram
    
    return render(request, 'predictions/process_image.html')

def results_view(request, mammogram_id):
    mammogram = Mammogram.objects.get(pk=mammogram_id)

    # get the results of the mammogram

    return render(request, 'predictions/results.html')