from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from registration import signals
from registration.backends.hmac.views import RegistrationView

class VariantRegistrationView(RegistrationView):
    """
    Custom implementation of django-registration RegistrationView.
    """

    def register(self, form):
        new_user = self.create_inactive_user(form)
        signals.user_registered.send(sender=self.__class__,
                                     user=new_user,
                                     request=self.request)
        return new_user

    def send_activation_email(self, user):
        """
        Send the activation email. The activation key is simply the
        username, signed using TimestampSigner.
        """
        activation_key = self.get_activation_key(user)
        context = self.get_email_context(activation_key)
        context.update({
            'user': user
        })
        subject = render_to_string(self.email_subject_template,
                                   context)
        # Force subject to a single line to avoid header-injection
        # issues.
        subject = ''.join(subject.splitlines())
        message_text = render_to_string(self.email_body_template,
                                        context)
        message_html = render_to_string('registration/activation_email.html',
                                        context)
        msg = EmailMultiAlternatives(subject, message_text,
                                     settings.DEFAULT_FROM_EMAIL,
                                     [user.email])
        msg.attach_alternative(message_html, "text/html")
        msg.send()
