"""variant URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.views.generic import RedirectView

from variant_app.views import index
from variant_app.registration_views import VariantRegistrationView

urlpatterns = [
    url(r'^$', index, name='home'),
    url(r'^variant/', include('variant_app.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^accounts/profile/$', RedirectView.as_view(pattern_name='variant_app:user_home', permanent=False)),
    url(r'^accounts/register/$', VariantRegistrationView.as_view(), name='registration_register'),
    url(r'^accounts/', include('registration.backends.hmac.urls')), # From django-registration.
    url(r'^silk/', include('silk.urls', namespace='silk')), # From django-silk
]
