from django.shortcuts import render, redirect
from .forms import MammogramForm
from .models import Mammogram


def upload_mammogram(request):
    if request.method == 'POST':
        form = MammogramForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('')
    else:
        form = MammogramForm()
    return render(request, 'predictions/upload_mammogram.html', {'form': form})

def processing_view(request, mammogram_id):
    mammogram = Mammogram.objects.get(pk=mammogram_id)

    # process the mammogram
    
    return render(request, 'predictions/process_mammogram.html')

def results_view(request, mammogram_id):
    mammogram = Mammogram.objects.get(pk=mammogram_id)

    # get the results of the mammogram

    return render(request, 'predictions/results.html')