from django.conf.urls import url

from . import views

app_name = 'variant_app'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^corpus/(?P<corpus_id>[0-9]+)/$', views.corpus, name='corpus'),
    url(r'^corpus/(?P<corpus_id>[0-9]+)/add/$', views.add_text, name='add_text'),
    url(r'^corpus/(?P<corpus_id>[0-9]+)/create_text/$', views.create_text, name='create_text'),
    url(r'^text/(?P<text_id>[0-9]+)/$', views.text, name='text'),
]
