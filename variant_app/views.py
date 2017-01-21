from django.contrib.auth import get_user_model
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector, TrigramSimilarity
from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist
from django.db import models, transaction
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound, HttpResponseServerError, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from django.template import loader
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from datetime import datetime
import json
import re
import time

from .models import Corpus, CollText, CollToken, Text, Token, Profile, Query
from .forms import RegistrationForm
import controllers

################
## Main Views ##
################

def index(request):
    return render(request, 'variant_app/index.html', {})

def user_home(request):
    context = {}
    if request.user.is_anonymous:
        if 'anon_corpus_ids' in request.session:
            corpus_ids = request.session['anon_corpus_ids']
            context['corpuses'] = []
            for pk in corpus_ids:
                try:
                    context['corpuses'].append(Corpus.objects.get(pk=pk))
                except Corpus.DoesNotExist:
                    continue
        else:
            context['corpuses'] = []
    else:
        context['corpuses'] = Corpus.objects.filter(user=request.user).order_by('-updated')
        context['favorites'] = Profile.objects.get(user=request.user).favorites.all().order_by('-updated')

    return render(request, 'variant_app/user_dashboard.html', context)

########################
## Explore and search ##
########################

def explore_home(request):
    num_recents = 8
    num_favorites = 8
    context = {}
    try:
        favorites = Corpus.objects.filter(
            is_public=True, user__is_active=True
        ).order_by('-n_favorites', '-updated')[:num_favorites]
    except Corpus.DoesNotExist:
        pass
    context['favorites'] = favorites
    try:
        recents = Corpus.objects.filter(
            is_public=True, user__is_active=True
        ).order_by('-created')[:num_recents]
    except Corpus.DoesNotExist:
        pass
    context['recents'] = recents    

    return render(request, 'variant_app/explore_home.html', context)

def search_results(request):
    if not 'query' in request.POST:
        return render(request, 'variant_app/search_results.html', {})
    query_str = request.POST['query'].strip().lower()

    # Very rudimentary search.
    # TODO: Integrate with Elasticsearch or Solr using django-haystack.
    # http://django-haystack.readthedocs.io/en/v2.4.1/tutorial.html
    users_limit = 3
    User = get_user_model()
    users = User.objects.annotate(
        similarity=TrigramSimilarity('username', query_str),
    ).filter(similarity__gt=0.3).order_by('-similarity')

    corpuses = Corpus.objects.filter(
        models.Q(corpus_name__icontains=query_str) |
        models.Q(author__icontains=query_str) |
        models.Q(preview__icontains=query_str))

    context = { 'users': users, 'corpuses': corpuses }
    return render(request, 'variant_app/search_results.html', context)

############
## Corpus ##
############

def corpus(request, corpus_id):
    corpus = get_object_or_404(Corpus, pk=corpus_id)
    corpus.n_views += 1
    corpus.save()

    if corpus.user != request.user and not corpus.is_public:
        return HttpResponseNotFound('Text not found or you do not have permissions to view this file.')

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

@transaction.atomic
def create_corpus(request):
    data = post_to_dict(request)
    name = data['corpus_name'].strip()
    content = data['content'].strip()
    date = parse_date(data['date'])
    date_end = parse_date(data['date_end'])

    # Error processing on the form values.
    emsg = name_error_message(name)
    if not request.user.is_anonymous:
        if Corpus.objects.filter(user__id=request.user.id, corpus_name=name).exists():
            emsg.append('You entered a name that is already in use.')
    if content == '':
        emsg.append('Content cannot be empty.')
    emsg += date_error_message(date, date_end)
    if len(data['description']) > 1000:
        emsg.append('Your description is too long, please limit it to 1000 characters.')
    data.update({ 'error_messages': emsg })
    if len(emsg) != 0:
        return render(request, 'variant_app/add_corpus.html', data)

    corpus, base_text = controllers.create_corpus(name, content)

    # Handle the form input.
    corpus.preview = content[:2000]
    if data['author'] != '':
        corpus.author = data['author'].strip().title()
    if data['description'] != '':
        corpus.description = data['description'].strip()
        base_text.description = data['description'].strip()
    if data['is_public_checkbox'] == 'on':
        corpus.is_public = True
    else:
        corpus.is_public = False
    if date:
        base_text.date = date
    if date_end:
        base_text.date_end = date_end
    if data['editor'] != '':
        base_text.editor = data['editor'].strip().title()
    corpus.save()
    base_text.save()

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

    Query(query=corpus.corpus_name.lower()).save()
    Query(query=corpus.preview[:100].lower()).save()

    return HttpResponseRedirect(reverse('variant_app:user_home'))

def delete_corpus(request, corpus_id):
    if not request.user.is_authenticated and not in_anon(request, corpus_id):
        return HttpResponseForbidden("Unauthenticated user tried to delete a corpus")

    if in_anon(request, corpus_id):
        try:
            Corpus.objects.get(pk=corpus_id, user=None).delete()
        except Corpus.DoesNotExist:
            pass
    else:
        try:
            Corpus.objects.get(pk=corpus_id, user=request.user).delete()
        except Corpus.DoesNotExist:
            pass
    
    return HttpResponseRedirect(reverse('variant_app:user_home'))

def corpus_public(request, corpus_id):
    corpus = get_object_or_404(Corpus, pk=corpus_id, user=request.user)
    corpus.is_public = not corpus.is_public
    corpus.save()
    return HttpResponse("Successfuly toggled corpus public status.")

@transaction.atomic
def corpus_favorite(request, corpus_id):
    if not request.user.is_authenticated:
        return HttpResponseForbidden("Unauthenticated users cannot favorite a corpus.")

    corpus = get_object_or_404(Corpus, pk=corpus_id)
    profile = get_object_or_404(Profile, user=request.user)
    if has_favorited(profile, corpus_id):
        profile.favorites.remove(corpus)
        corpus.n_favorites -= 1
    else:
        profile.favorites.add(corpus)
        corpus.n_favorites += 1
    corpus.save()
    profile.save()

    return HttpResponse("Successfuly favorited corpus.")

###############
## Coll Text ##
###############

def coll_text(request, corpus_id):
    coll_text = get_object_or_404(CollText, corpus__id=corpus_id)
    corpus = get_object_or_404(Corpus, pk=corpus_id)

    context = {}
    if request.user != corpus.user:
        if not corpus.is_public:
            return HttpResponseForbidden("Sorry, could not find the text you were looking for.")
        elif not request.user.is_anonymous:
            profile = get_object_or_404(Profile, user=request.user)
            is_fav = has_favorited(profile, corpus_id)
            context['is_fav'] = is_fav
    try:
        texts = Text.objects.filter(corpus__id=corpus_id)
    except Text.DoesNotExist:
        texts = []
    
    context.update({ 'corpus': corpus, 'coll_text': coll_text,
                     'texts': texts, 'in_at': in_anon(request, coll_text.corpus.id) })
    return render(request, 'variant_app/coll_text.html', context)

def coll_text_content(request, corpus_id):
    coll_text = get_object_or_404(CollText, corpus__id=corpus_id)
    num_texts = float(Text.objects.filter(corpus__id=corpus_id).count())

    text_meta = {}
    text_meta['tokens'] = []
    for token in coll_text.tokens().order_by('seq'):
        token_meta = {}
        token_meta['word'] = token.word
        token_meta['seq'] = token.seq
        if num_texts <= 1:
            token_meta['variability'] = 1
        else:
            token_meta['variability'] = token.variability / (num_texts-1)
        text_meta['tokens'].append(token_meta)

    return HttpResponse(json.dumps(text_meta))

@transaction.atomic
@require_http_methods([ 'POST' ])
def post_word(request, corpus_id):
    data = json.loads(request.body)
    word = data['word']
    coll_token_seq = data['coll_token_seq']
    text_name = data['text_name']

    try:
        if in_anon(request, corpus_id):
            coll_token = CollToken.objects.get(corpus__user=None,
                                               corpus__id=corpus_id,
                                               seq=coll_token_seq)
            all_tokens = Token.objects.filter(corpus__user=None,
                                              corpus__id=corpus_id,
                                              coll_token_seq=coll_token_seq)
        else:
            coll_token = CollToken.objects.get(corpus__user=request.user,
                                               corpus__id=corpus_id,
                                               seq=coll_token_seq)
            all_tokens = Token.objects.filter(corpus__user=request.user,
                                              corpus__id=corpus_id,
                                              coll_token_seq=coll_token_seq)
    except (CollToken.DoesNotExist, Token.DoesNotExist):
        coll_token = None
        all_tokens = []

    if coll_token != None:
        coll_token.word = word
        coll_token.save()

    for token in all_tokens:
        if token.text.text_name == text_name:
            token.is_base = True
        else:
            token.is_base = False
        token.save()

    return HttpResponse("Success")


def coll_text_tokens(request, corpus_id, seq_start, seq_end, seq_center):
    all_tokens = Token.objects.filter(corpus__id=corpus_id,
                                      coll_token_seq__gte=int(seq_start),
                                      coll_token_seq__lte=int(seq_end)).order_by('text', 'seq')
    meta = {}
    meta['sequences'] = []
    meta['coll_token_seq'] = int(seq_center);
    curr_text = None
    curr_word = ''
    tokens = []
    for token in all_tokens:
        word = token.word.replace('\n', ' / ')
        if curr_text == None:
            curr_text = token.text
        elif curr_text != token.text:
            meta['sequences'].append({ 'tokens': tokens,
                                       'text_name': curr_text.text_name,
                                       'is_base': curr_text.is_base })
            curr_text = token.text
            tokens = []
        tokens.append({ 'word': word,
                        'is_center': token.coll_token_seq == int(seq_center),
                        'is_coll': token.is_base })
    if curr_text != None:
        meta['sequences'].append({ 'tokens': tokens,
                                   'text_name': curr_text.text_name,
                                   'is_base': curr_text.is_base })
    return HttpResponse(json.dumps(meta))

##########
## Text ##
##########

def text(request, text_id):
    text = get_object_or_404(Text, pk=text_id)
    base_text = get_object_or_404(Text, corpus=text.corpus, is_base=True)
    context = { 'text': text, 'base_text': base_text,
                'in_at': in_anon(request, text.corpus.id) }
    return render(request, 'variant_app/text.html', context)

def text_content(request, text_id):
    text = get_object_or_404(Text, pk=text_id)

    if text.corpus.user != request.user and not text.corpus.is_public:
        return HttpResponseNotFound('Text not found or you do not have permissions to view this file.')

    text_meta = {}
    text_meta['name'] = text.text_name
    text_meta['tokens'] = []
    for token in text.tokens().order_by('seq'):
        token_meta = {}
        token_meta['word'] = token.word
        token_meta['seq'] = token.seq
        token_meta['coll_token_seq'] = token.coll_token_seq
        token_meta['variability'] = token.variability
        text_meta['tokens'].append(token_meta)

    return HttpResponse(json.dumps(text_meta))

def add_text(request, corpus_id):
    corpus = get_object_or_404(Corpus, pk=corpus_id)
    context = { 'corpus': corpus }
    return render(request, 'variant_app/add_text.html', context)

@transaction.atomic
def create_text(request, corpus_id):
    data = post_to_dict(request)
    print(data)
    corpus = get_object_or_404(Corpus, pk=corpus_id)
    text_name = data['text_name'].strip()
    content = data['content'].strip()
    date = parse_date(data['date'])
    date_end = parse_date(data['date_end'])

    # Error processing on the form values.
    emsg = name_error_message(text_name)
    if text_name.lower() == "base text":
        emsg.append('You cannot call a variant "Base Text".')
    if Text.objects.filter(corpus__id=corpus.id, text_name=text_name).exists():
        emsg.append('Text name for this corpus has already been used.')
    if content == '':
        emsg.append('Content cannot be empty.')
    emsg += date_error_message(date, date_end)
    if len(data['description']) > 1000:
        emsg.append('Your description is too long, please limit it to 1000 characters.')
    data.update({ 'corpus': corpus, 'error_messages': emsg })
    if len(emsg) != 0:
        return render(request, 'variant_app/add_text.html', data)

    text = controllers.create_text(corpus, text_name, content)

    # Handle the form input.
    if data['description'] != '':
        text.description = data['description'].strip()
    if date:
        text.date = date
    if date_end:
        text.date_end = date_end
    if data['editor'] != '':
        text.editor = data['editor'].strip().title()
    text.save()

    Query(query=text.text_name.lower()).save()

    return HttpResponseRedirect(reverse('variant_app:corpus', args=(corpus.id,)))

def delete_text(request, text_id):
    try:
        text = Text.objects.get(pk=text_id)
        corpus_id = text.corpus.id
    except Text.DoesNotExist:
        return HttpResponseRedirect(reverse('variant_app:user_home'))

    if not request.user.is_authenticated and not in_anon(request, corpus_id):
        return HttpResponseForbidden("Unauthenticated user tried to delete a corpus")

    if request.user.is_authenticated and text.corpus.user == request.user:
        text.delete()
    if in_anon(request, corpus_id) and text.corpus.user == None:
        text.delete()

    return HttpResponseRedirect(reverse('variant_app:corpus', args=(corpus_id,)))

@transaction.atomic
@require_http_methods([ 'POST' ])
def manual_coll(request, text_id):
    data = json.loads(request.body);
    if not 'seq' in data:
        return HttpResponseBadRequest("No seq given.")
    seq = int(data['seq'])
    if not 'coll_token_seq' in data:
        return HttpResponseBadRequest("No coll_token_seq given.")
    coll_token_seq = int(data['coll_token_seq'])

    if request.user.is_anonymous:
        try:
            text = Text.objects.get(pk=text_id, corpus__user=None)
        except Text.DoesNotExist:
            return HttpResponseForbidden("Could not find text or incorrect permissions.")
        if not in_anon(request, text.corpus.id):
            return HttpResponseForbidden("Could not find text or incorrect permissions.")
    else:
        try:
            text = Text.objects.get(pk=text_id, corpus__user=request.user)
        except Text.DoesNotExist:
            return HttpResponseForbidden("Could not find text or incorrect permissions.")

    try:
        token = Token.objects.get(seq=seq, text=text)
    except Token.DoesNotExist:
        return HttpResponseNotFound("Could not find token.")
    try:
        coll_token = CollToken.objects.get(seq=coll_token_seq, corpus=text.corpus)
        prev_coll_token = CollToken.objects.get(seq=token.coll_token_seq, corpus=text.corpus)
    except CollToken.DoesNotExist:
        return HttpResponseNotFound("Could not find coll token.")

    prev_coll_token.variability -= controllers.token_similarity_score(prev_coll_token, token)
    prev_coll_token.save()

    token.coll_token_seq = coll_token_seq
    token.variability = controllers.token_similarity_score(coll_token, token)
    token.save()

    coll_token.variability += token.variability
    coll_token.save()

    return HttpResponse("Successful manual collation.")


#######################
## Utility functions ##
#######################

def in_anon(request, corpus_id):
    return (request.user.is_anonymous and
            'anon_corpus_ids' in request.session and
            int(corpus_id) in request.session['anon_corpus_ids'])

def name_error_message(name):
    emsg = []
    name = name.strip()
    if len(name) == 0:
        emsg.append('Please enter a name.')
    elif len(name) > 100:
        emsg.append('Please limit the name to less than 100 characters.')
    return emsg

def date_error_message(date, date_end):
    emsg = []
    if date == None:
        emsg.append('Date provided is not properly formatted (YYYY-MM-DD).')
    if date_end == None:
        emsg.append('End date provided is not properly formatted (YYYY-MM-DD).')

    if date_end:
        if date == False:
            emsg.append('You provided an end date but not a start date')
        elif date_end < date:
            emsg.append('The end date provided cannot be before the start date.')

    return emsg

def post_to_dict(request):
    # Default dict function creates list, not unique values.
    data = {}
    for key in request.POST:
        if 'csrf' in key:
            continue
        assert(not key in data)
        data[key] = request.POST[key]
    return data

def parse_date(date_str):
    if date_str.strip() == '':
        return False

    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        try:
            date = datetime.strptime(date_str, '%Y-%m')
        except ValueError:
            try:
                date = datetime.strptime(date_str, '%Y')
            except ValueError:
                date = None
    return date

def has_favorited(profile, corpus_id):
    return profile.favorites.filter(pk=corpus_id).exists()
