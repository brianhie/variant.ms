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

    create_text(corpus, corpus_name, content)

    return corpus

@transaction.atomic
def create_text(corpus, text_name, content):
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

    collate(coll_text, tokens)
    return text


######################################
## Helper functions for tokenize(). ##
######################################

def _split(content):
    for a in re.split(r'(\s+)', content):
        if a.strip() == '':
            yield a
            continue
        for b in re.split(ur'([\.?!,:;\-–—―=…\}\]\)\"”’]+$|^[\{\[\(\"“‘]+)',
                          a, re.UNICODE):
            if b != '':
                yield b

def tokenize(text, content):
    if content == '':
        return []
    if isinstance(content, str):
        content = unicode(content, 'utf8')
    tokens = []
    for seq, word in enumerate(_split(content)):
        token = Token(word=word,
                      corpus=text.corpus,
                      text=text,
                      coll_token=None, # Assigned in collate() below.
                      seq=seq)
        tokens.append(token)
    return tokens

##############################################
## Helper functions for create_coll_text(). ##
##############################################

#@transaction.atomic
def init_coll_text(corpus, base_tokens):
    coll_text = CollText(corpus=corpus)
    coll_text.save()

    for seq, token in enumerate(base_tokens):
        coll_token = CollToken(word=token.word,
                               seq=seq,
                               corpus=corpus,
                               coll_text=coll_text)
        coll_token.save()
        token.coll_token = coll_token
        token.save()
    
    return coll_text

#####################################
## Helper functions for collate(). ##
#####################################

def _isspace(s):
    return s.strip() == ''

def _ispunc(s):
    return s.rstrip(string.punctuation) == ''

def _token_similarity(a, b):
    # Strings are a case insensitive match.
    # Match any whitespace to any whitespace.
    if a.word.lower().strip() == b.word.lower().strip():
        return True

    # Make it impossible for words to map to whitespace.
    if ((_isspace(a.word) and not _isspace(b.word)) or
        (not _isspace(a.word) and _isspace(b.word))):
        return False

    # Make it impossible for words to map to punctuation.
    if _ispunc(a.word) and _ispunc(b.word):
        return True
    if ((_ispunc(a.word) and not _ispunc(b.word)) or
        (not _ispunc(a.word) and _ispunc(b.word))):
        return False

    # Strings sound alike (approximate phonetic match).
    if a.word.isalpha() and b.word.isalpha():
        if jf.metaphone(a.word) == jf.metaphone(b.word):
            return True
        if jf.soundex(a.word) == jf.soundex(b.word):
            return True
        if jf.nysiis(a.word) == jf.nysiis(b.word):
            return True
        if jf.match_rating_codex(a.word) == jf.match_rating_codex(b.word):
            return True

    # Use scaled Jaro-Winkler distance.
    return jf.jaro_winkler(a.word, b.word) > 0.8


@transaction.atomic
def collate(coll_text, tokens):
    try:
        coll_tokens = CollToken.objects.filter(coll_text__id=coll_text.id)
    except CollToken.DoesNotExist:
        sys.stderr.write('No coll tokens for corpus ' + str(coll_text.corpus.id) + '\n')
        return

    link_prev = []
    coll_iter = vc.collate(coll_tokens, tokens, _token_similarity)
    for coll_token, token, status in coll_iter:
        if status == 'match':
            # Link token to the coll token.
            token.coll_token = coll_token
            token.is_base = True
            token.save()
            # Also link inserted tokens.
            for to_link in link_prev:
                to_link.coll_token = coll_token
                to_link.is_base = True
                to_link.save()
                link_prev = []
        elif status == 'delete':
            # No new tokens need to be linked.
            if coll_token:
                for to_link in link_prev:
                    to_link.coll_token = coll_token
                    to_link.is_base = True
                    to_link.save()
                link_prev = []
        elif status == 'insert':
            # Inserted tokens map to first coll token.
            # (This loops iterates backwards through the texts.)
            link_prev.append(token)
        else:
            assert(False)

    try:
        coll_token = CollToken.objects.get(coll_text=coll_text, seq=0)
        for to_link in link_prev:
            to_link.coll_token = coll_token
            to_link.is_base = True
            to_link.save()
    except CollToken.DoesNotExist:
        pass


