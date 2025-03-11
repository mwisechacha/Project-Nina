from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth import views as auth_views
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm, RequestDemoForm
from predictions.models import Radiologist
from django.core.mail import EmailMessage
from django.conf import settings
import os


# home view
def home_view(request):
    return render(request, 'users/home.html')

# register view
def register_view(request):
    image_id = request.GET.get('image_id')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            Radiologist.objects.create(user=user)
            messages.success(request, 'Account created successfully. Please login.')
            if image_id:
                return HttpResponseRedirect(reverse('upload_mammogram', f'?image_id={image_id}'))
            else:
                return redirect('login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = RegisterForm()
    return render(request, 'users/register.html', {'form': form})

# login view
class CustomLoginView(auth_views.LoginView):
    template_name = 'users/login.html'
    redirect_authenticated_user = True

    def form_invalid(self, form):
        messages.error(self.request, 'Invalid username or password.')
        return super().form_invalid(form)

# demo view
def request_demo_view(request):
    if request.method == 'POST':
        form = RequestDemoForm(request.POST)
        if form.is_valid():
            # save to db and send and email
            form.save()

            # get user's email
            user_name = form.cleaned_data.get('name')
            user_email = form.cleaned_data.get('email')

            # prepare email
            subject = 'ProjectNina: Video Demo'
            message = (
                f'Hi {user_name},\n\n'
                'Thank you for requesting a demo of ProjectNina. '
                'Please Find the demo video attached to this email.\n\n'
                'Best regards,\n'
                'ProjectNina Team'
            )
            from_email = 'angieschacha@gmail.com'
            recipient_list = [user_email]

            # demo video
            email = EmailMessage(
                subject=subject,
                body=message,
                from_email=from_email,
                to=recipient_list,
            )
            demo_video_path = os.path.join(settings.BASE_DIR, 'static', 'users', 'demo.mp4')
            email.attach_file(demo_video_path)

            # send email
            try:
                email.send()
                messages.success(request, 'Request submitted successfully. Check your email for the demo video.')
            except Exception as e:
                messages.error(request, 'An error occurred while sending the email.')

            return redirect('home')
        else:
            messages.error(request, 'Please correct the errors.')
    else:
        form = RequestDemoForm()
    return render(request, 'users/demo.html', {'form': form})

