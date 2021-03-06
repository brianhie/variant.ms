# -*- coding: utf-8 -*-

from django.db import transaction
import jellyfish as jf
import re
import string
import sys
import variant_collate as vc

from models import Corpus, CollText, Text, CollToken, Token


@transaction.atomic
def create_corpus(corpus_name, content):
    corpus = Corpus(corpus_name=corpus_name)
    corpus.save()

    base_text = create_text(corpus, corpus_name, content)

    return corpus, base_text

@transaction.atomic
def create_text(corpus, text_name, content, debug=False):
    text = Text(text_name=text_name, corpus=corpus)
    text.save()
    tokens = tokenize(text, content)
    try:
        coll_text = CollText.objects.get(corpus__id=corpus.id)
    except CollText.DoesNotExist:
        # Coll text does not exist, use it as base text.
        coll_text = init_coll_text(corpus, tokens)
        text.is_base = True
        text.save()
        return text
    collate(coll_text, tokens, debug=debug)
    return text

def tokenize(text, content):
    if content == '':
        return []
    if isinstance(content, str):
        content = unicode(content, 'utf8')
    tokens = []
    for seq, word in enumerate(vc.tokenize(content)):
        token = Token(word=word,
                      corpus=text.corpus,
                      text=text,
                      seq=seq)
        tokens.append(token)
    return tokens

@transaction.atomic
def init_coll_text(corpus, base_tokens):
    coll_text = CollText(corpus=corpus)
    coll_text.save()

    coll_tokens = []
    tokens = []
    for seq, token in enumerate(base_tokens):
        coll_token = CollToken(word=token.word,
                               seq=seq,
                               corpus=corpus,
                               coll_text=coll_text)
        coll_tokens.append(coll_token)
        token.coll_token_seq = seq
        token.is_base = True
        tokens.append(token)

    CollToken.objects.bulk_create(coll_tokens)
    Token.objects.bulk_create(tokens)
    
    return coll_text

def _isspace(s):
    return s.isspace()

def _ispunc(s):
    return re.sub(vc.split_re, '', s) == ''

def _match_ampersand(a, b):
    if ((a == '&' and b == 'and') or
        (a == 'and' and b == '&')):
        return True

def _token_similarity(a, b):
    return _word_similarity_score(a.word, b.word) > 0.8

def token_similarity_score(a, b):
    return _word_similarity_score(a.word, b.word)

def _word_similarity_score(a, b):
    if a == b:
        return 1.

    # Case and whitespace insenstive comparison.
    if a.lower().strip() == b.lower().strip():
        return 0.95

    # Penalize whitespace matching to non-whitespace.
    if ((_isspace(a) and not _isspace(b)) or
        (not _isspace(a) and _isspace(b))):
        return 0

    # Exceptions to punctuation.
    if _match_ampersand(a, b):
        return 0.85
    # Penalize punctuation matching to non-punctuation.
    if _ispunc(a) and _ispunc(b):
        return 0.95
    if ((_ispunc(a) and not _ispunc(b)) or
        (not _ispunc(a) and _ispunc(b))):
        return 0

    # Problems with phonetic match functions segfaulting on
    # empty strings. Also beneficial to match strings with
    # no alpha characters to each other (e.g., line numbers).
    a_alpha = u''.join([ c for c in a if c.isalpha() ])
    b_alpha = u''.join([ c for c in b if c.isalpha() ])
    if a_alpha == '' and b_alpha == '':
        return 0.85

    # Strings sound alike (approximate phonetic match).
    if jf.match_rating_comparison(a_alpha, b_alpha):
        return 0.9
    if jf.metaphone(a_alpha) == jf.metaphone(b_alpha):
        return 0.9
    if jf.soundex(a_alpha) == jf.soundex(b_alpha):
        return 0.9
    if jf.nysiis(a_alpha) == jf.nysiis(b_alpha):
        return 0.9

    # Use scaled Jaro-Winkler distance.
    return jf.jaro_winkler(a, b)

@transaction.atomic
def collate(coll_text, tokens, debug=False):
    try:
        coll_tokens = CollToken.objects.filter(coll_text__id=coll_text.id).order_by('seq')
    except CollToken.DoesNotExist:
        sys.stderr.write('No coll tokens for corpus ' + str(coll_text.corpus.id) + '\n')
        return

    coll_token_seq = 0
    coll_token_prev_seq = -1
    for coll_token, token, status in vc.collate(coll_tokens, tokens,
                                                _token_similarity):
        if status == 'match':
            if debug:
                assert(coll_token.seq == coll_token_seq)
            token.coll_token_seq = coll_token.seq
            token.variability = token_similarity_score(coll_token, token)
            coll_token.variability += token.variability
            coll_token.save()
            coll_token_prev_seq = coll_token.seq
            coll_token_seq += 1
        elif status == 'delete':
            if debug:
                assert(coll_token.seq == coll_token_seq)
            coll_token_prev_seq = coll_token.seq
            coll_token_seq += 1
        elif status == 'insert':
            token.coll_token_seq = coll_token_prev_seq
        else:
            assert(False)

    Token.objects.bulk_create(tokens)
