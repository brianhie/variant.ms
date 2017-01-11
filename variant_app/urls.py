from django.conf.urls import include, url
from django.views.generic.base import RedirectView

from . import views

app_name = 'variant_app'
urlpatterns = [
    url(r'^$', views.index, name='index'),

    url('^', include('django.contrib.auth.urls')),
    url(r'^accounts/profile$', RedirectView.as_view(pattern_name='user_home', permanent=False)),

    url(r'^home/', views.user_home, name='user_home'),

    url(r'^corpus/(?P<corpus_id>[0-9]+)/$', views.corpus, name='corpus'),
    url(r'^corpus/add$', views.add_corpus, name='add_corpus'),
    url(r'^corpus/post$', views.create_corpus, name='create_corpus'),

    url(r'^text/(?P<text_id>[0-9]+)/$', views.text, name='text'),
    url(r'^text/(?P<corpus_id>[0-9]+)/add/$', views.add_text, name='add_text'),
    url(r'^text/(?P<corpus_id>[0-9]+)/post/$', views.create_text, name='create_text'),
]
