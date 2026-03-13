from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings

def send_welcome_email(user) -> None:
    """
    Send a welcome email to the newly registered user.
    The email content is rendered from templates and supports multiple languages based on the user's preferred language.
    """
    lang = getattr(user, 'preferred_language', 'en') or 'en'
    
    suffix = f"_{lang}" if lang in ['ru', 'kk'] else ""
    
    subject_template = f'emails/welcome/subject{suffix}.txt'
    body_template = f'emails/welcome/body{suffix}.txt'
    
    context = {
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
    }
    
    subject = render_to_string(subject_template, context).strip()
    body = render_to_string(body_template, context).strip()
    
    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    email.send(fail_silently=True)