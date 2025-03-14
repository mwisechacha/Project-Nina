from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import views as auth_views
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.template.loader import render_to_string
from .forms import RegisterForm, RequestDemoForm
from .tokens import email_token
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
            user = form.save(commit=False)
            user.is_active = False
            user.set_password(form.cleaned_data.get('password1'))
            user.save()

            # send email verification
            current_site = get_current_site(request)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = email_token.make_token(user)
            mail_subject = 'Activate Your Account'
            message = render_to_string('users/email_verification.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': uid,
                'token': token,
                'image_id': image_id,
            })
            email = EmailMessage(mail_subject, message, to=[user.email])
            email.send()

            messages.success(request, f'Account created for {user.username}. Please check your email to activate your account.')

            if not Radiologist.objects.filter(user=user).exists():
                Radiologist.objects.create(user=user)

            return render(request, 'users/email_sent.html', {'email': user.email})       
    else:
        form = RegisterForm()
    return render(request, 'users/register.html', {'form': form, 'image_id': image_id})

User = get_user_model()

def activate_account(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and email_token.check_token(user, token):
        user.is_active = True
        user.save()
        return render(request, 'users/email_verification_success.html', {'user': user})
    else:
        return render(request, 'users/email_verification_failed.html')
    
def resend_activation_email(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            if user.is_active:
                messages.info(request, "Your account is already activated.")
                return redirect('login')

            # new activation lik
            current_site = get_current_site(request)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = email_token.make_token(user)

            mail_subject = 'Resend: Activate Your Account'
            message = render_to_string('users/email_verification.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': uid,
                'token': token,
            })
            email = EmailMessage(mail_subject, message, to=[user.email])
            email.send()

            return render(request, 'users/resend_email_success.html', {'email': user.email})
        except User.DoesNotExist:
            messages.error(request, 'User with that email does not exist.')
            return redirect('resend_ativation_email')
        
    return render(request, 'users/resend_activation_email.html')


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

