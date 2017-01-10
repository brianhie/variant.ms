from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import get_object_or_404, render
from django.template import loader
from django.urls import reverse
import re
import json

from .models import Corpus, CollText, Text
import controllers

def index(request):
    corpuses = Corpus.objects.all()
    
    context = { 'corpuses': corpuses }
    return render(request, 'variant_app/user_dashboard.html', context)

############
## Corpus ##
############

def corpus(request, corpus_id):
    corpus = get_object_or_404(Corpus, pk=corpus_id)
    try:
        coll_text = CollText.objects.get(corpus__id=corpus_id)
    except CollText.DoesNotExist:
        coll_text = None
    try:
        texts = Text.objects.filter(corpus__id=corpus_id)
    except Text.DoesNotExist:
        texts = []
    context = { 'corpus': corpus, 'coll_text': coll_text, 'texts': texts }
    return render(request, 'variant_app/corpus.html', context)

def add_corpus(request):
    context = {}
    return render(request, 'variant_app/add_corpus.html', context)

def create_corpus(request):
    name = request.POST['corpus_name'].strip()
    content = request.POST['content'].strip()

    emsg = name_error_message(name)
    if Corpus.objects.filter(corpus_name=name).exists():
        emsg.append('This name is already in use.')
    if content == '':
        emsg.append('Content cannot be empty.')
    if len(emsg) != 0:
        return render(request, 'variant_app/add_corpus.html',
                      { 'error_messages': emsg })

    controllers.create_corpus(name, content)

    return HttpResponseRedirect(reverse('variant_app:index'))

##########
## Text ##
##########

def text(request, text_id):
    text = get_object_or_404(Text, pk=text_id)
    data =  serializers.serialize('json', text.tokens())
    json_data = json.loads(data)
    content = ''
    for d in json_data:
        content += d['fields']['word']
    context = { 'data': data, 'content': content }
    return render(request, 'variant_app/text.html', context)

def add_text(request, corpus_id):
    corpus = get_object_or_404(Corpus, pk=corpus_id)
    context = { 'corpus': corpus }
    return render(request, 'variant_app/add_text.html', context)

def create_text(request, corpus_id):
    corpus = get_object_or_404(Corpus, pk=corpus_id)
    text_name = request.POST['text_name'].strip()
    content = request.POST['content'].strip()

    # Error processing on the form values.
    emsg = name_error_message(text_name)
    if Text.objects.filter(corpus__id=corpus.id, text_name=text_name).exists():
        emsg.append('Text name for this corpus has already been used.')
    if content == '':
        emsg.append('Content cannot be empty.')
    if len(emsg) != 0:
        return render(request, 'variant_app/add_text.html',
                      { 'corpus': corpus,
                        'error_messages': emsg })


    controllers.create_text(corpus, text_name, content)

    return HttpResponseRedirect(reverse('variant_app:corpus', args=(corpus.id,)))

#######################
## Utility functions ##
#######################

def name_error_message(name):
    emsg = []
    name = name.strip()
    if len(name) == 0:
        emsg.append('Please enter a name.')
    elif len(name) > 100:
        emsg.append('Please limit the name to less than 100 characters.')
    else:
        stripped_name = re.sub(r'[ \.\-_]', '', name)
        if not stripped_name.isalnum():
            emsg.append('You name can only contain the characters ' +
                        '.-_ and letters, numbers, and spaces.')
    return emsg
