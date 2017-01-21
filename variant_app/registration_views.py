from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.template.loader import render_to_string
from registration import signals
from registration.backends.hmac.views import RegistrationView
from registration.forms import RegistrationForm

from .models import Corpus, Profile, Query

class VariantRegistrationForm(RegistrationForm):
    # Implement case insensitive username validation.
    def clean(self):
        User = get_user_model()
        username_value = self.cleaned_data.get(User.USERNAME_FIELD)
        if username_value is not None and User.objects.filter(username__iexact=username_value).exists():
            self.add_error(User.USERNAME_FIELD,
                           ValidationError("A user with that username already exists."))

        super(VariantRegistrationForm, self).clean()

class VariantRegistrationView(RegistrationView):
    """
    Custom implementation of django-registration RegistrationView.
    """
    form_class = VariantRegistrationForm

    @transaction.atomic
    def register(self, form):
        new_user = self.create_inactive_user(form)

        profile = Profile()
        profile.user = new_user
        profile.save()

        Query(query=corpus.preview[:100].lower()).save()

        # Handle corpuses that may have been created during
        # an initial anonymous session.
        if 'anon_corpus_ids' in self.request.session:
            for pk in self.request.session['anon_corpus_ids']:
                try:
                    corpus = Corpus.objects.get(pk=pk, user=None)
                except Corpus.DoesNotExist:
                    continue
                corpus.user = new_user
                corpus.save()

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

