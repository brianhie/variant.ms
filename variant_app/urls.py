from django.conf.urls import include, url
from django.views.generic.base import RedirectView

from . import views

app_name = 'variant_app'
urlpatterns = [
    url(r'^$', views.index, name='index'),

    url(r'^home/', views.user_home, name='user_home'),

    url(r'^corpus/(?P<corpus_id>[0-9]+)/$', views.corpus, name='corpus'),
    url(r'^corpus/add/$', views.add_corpus, name='add_corpus'),
    url(r'^corpus/post/$', views.create_corpus, name='create_corpus'),

    url(r'^corpus/(?P<corpus_id>[0-9]+)/coll/$', views.coll_text, name='coll_text'),
    url(r'^corpus/(?P<corpus_id>[0-9]+)/coll/content/$', views.coll_text_content,
        name='coll_text_content'),
    url(r'^corpus/(?P<corpus_id>[0-9]+)/coll/tokens/(?P<seq>[0-9]+)/$',
        views.coll_text_tokens, name='coll_text_tokens'),

    url(r'^text/(?P<text_id>[0-9]+)/$', views.text, name='text'),
    url(r'^text/(?P<text_id>[0-9]+)/content/$', views.text_content, name='text_content'),
    url(r'^text/(?P<corpus_id>[0-9]+)/add/$', views.add_text, name='add_text'),
    url(r'^text/(?P<corpus_id>[0-9]+)/post/$', views.create_text, name='create_text'),
]
