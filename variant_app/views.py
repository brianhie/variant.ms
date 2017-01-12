from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound, HttpResponseServerError
from django.shortcuts import get_object_or_404, render
from django.template import loader
from django.urls import reverse
import json
import re

from .models import Corpus, CollText, Text
from .forms import RegistrationForm
import controllers

def index(request):
    return render(request, 'variant_app/index.html', {})

def user_home(request):
    if request.user.is_anonymous:
        if 'anon_corpus_ids' in request.session:
            corpus_ids = request.session['anon_corpus_ids']
            corpuses = []
            for pk in corpus_ids:
                try:
                    corpuses.append(Corpus.objects.get(pk=pk))
                except Corpus.DoesNotExist:
                    continue
        else:
            corpuses = []
    else:
        corpuses = Corpus.objects.filter(user=request.user)

    context = { 'corpuses': corpuses }
    return render(request, 'variant_app/user_dashboard.html', context)

############
## Corpus ##
############

def corpus(request, corpus_id):
    corpus = get_object_or_404(Corpus, pk=corpus_id)
    try:
        coll_text = CollText.objects.get(corpus=corpus)
    except CollText.DoesNotExist:
        coll_text = None
    try:
        texts = Text.objects.filter(corpus=corpus)
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

    corpus = controllers.create_corpus(name, content)

    # Handle corpus creation for anonymous user sessions.
    if request.user.is_anonymous:
        if 'anon_corpus_ids' in request.session:
            prev_ids = request.session['anon_corpus_ids']
        else:
            prev_ids = []
        prev_ids.append(corpus.id)
        request.session['anon_corpus_ids'] = prev_ids
    else:
        corpus.user = request.user
        corpus.save()

    return HttpResponseRedirect(reverse('variant_app:user_home'))

##########
## Text ##
##########

def text(request, text_id):
    text = get_object_or_404(Text, pk=text_id)
    base_text = get_object_or_404(Text, corpus=text.corpus, is_base=True)
    context = { 'text': text, 'base_text': base_text }
    return render(request, 'variant_app/text.html', context)

def text_content(request, text_id):
    text = get_object_or_404(Text, pk=text_id)
    if (not text.corpus.id in request.session['anon_corpus_ids'] and
        text.corpus.user != request.user and
        not text.corpus.is_public):
        return HttpResponseNotFound('Text not found or you do not have permissions to view this file.')

    text_meta = {}
    text_meta['name'] = text.text_name
    if text.date:
        text_meta['date'] = text.date.strftime('%m/%d/%Y')
    else:
        text_meta['date'] = None
    text_meta['tokens'] = []
    for token in text.tokens().order_by('seq'):
        token_meta = {}
        token_meta['word'] = token.word
        token_meta['seq'] = token.coll_token.seq
        text_meta['tokens'].append(token_meta)

    return HttpResponse(json.dumps(text_meta))

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
