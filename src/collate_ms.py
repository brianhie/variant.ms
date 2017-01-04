# -*- coding: utf-8 -*-

import codecs
import collate as coll
import jellyfish as jf
from nltk.tokenize.moses import MosesTokenizer
import os
import re
import sys

class Text(coll.Coll):
    def __init__(self, text_id):
        super(Text, self).__init__([])
        self.text_id = text_id
        self.title = '(no title)'
        self.content = ''

    def tokenize(self, content=u''):
        self.content = content
        if content == '':
            return
        self.sequence.append(Token(u'', self.text_id))
        for a in re.split(r'(\s+)', content):
            if a.strip() == '':
                self.sequence.append(Token(a, self.text_id))
                continue
            for b in re.split(ur'([\.?!,:;\-–—―…\"”’]+$|^[\"“‘]+)',
                              a, re.UNICODE):
                self.sequence.append(Token(b, self.text_id))
#        tok = MosesTokenizer()
#        for t in tok.tokenize(content):
#            token = Token(t, self.text_id)
#            self.sequence.append(token)


    def add_token(self, token):
        self.sequence.append(token)

    def push_token(self, token):
        self.sequence.insert(0, token)

class Token(coll.CollElem):
    def __init__(self, base_word, base_text_id):
        self._words = {}
        self.base_word = base_word
        self.base_text_id = base_text_id
        self.add(base_word, base_text_id)
        super(Token, self).__init__()
        
    def add(self, word, text_id):
        self._words[text_id] = word

    def get(self, text_id):
        return self._words[text_id]

    def iter_words(self):
        for text_id in self._words:
            yield self._words[text_id]

    def iter_word_texts(self):
        for text_id in self._words:
            yield self._words[text_id], text_id


def token_similarity(a, b):
    # Strings are a case insensitive match.
    if a.base_word.strip() == b.base_word.strip():
        return 1.

    # Strings sound alike (approximate phonetic match).
    if a.base_word.isalpha() and b.base_word.isalpha():
        if jf.metaphone(a.base_word) == jf.metaphone(b.base_word):
            return 0.9
        if jf.soundex(a.base_word) == jf.soundex(b.base_word):
            return 0.9
        if jf.nysiis(a.base_word) == jf.nysiis(b.base_word):
            return 0.9
        if jf.match_rating_codex(a.base_word) == jf.match_rating_codex(b.base_word):
            return 0.9

    # Penalize words mapping to non alpha numerics.
    if ((a.base_word.isalpha() and not b.base_word.isalpha()) or
        (not a.base_word.isalpha() and b.base_word.isalpha())):
        return -1.

    # Use scaled Jaro-Winkler distance.
    return (jf.jaro_winkler(a.base_word, b.base_word) * 2) - 1

def collate_text(master, text):
    new_master = Text('__COLL__')
    to_insert = ''
    for token_a, token_b, status in coll.collate(master, text, token_similarity):
        if status == 'match':
            assert(token_b.base_text_id == text.text_id)
            token_a.add(token_b.base_word + to_insert, token_b.base_text_id)
            new_master.push_token(token_a)
            to_insert = ''
        elif status == 'delete':
            token_a.add('' + to_insert, text.text_id)
            new_master.push_token(token_a)
            to_insert = ''
        elif status == 'insert':
            to_insert = to_insert + ' ' + token_b.base_word
        else:
            assert(False)
    if to_insert != '':
        new_master.sequence[0].add(to_insert.lstrip(' ') + ' ' +
                                   new_master.sequence[0].get(),
                                   text.text_id)
    return new_master

def load_text(text_dir, text_path):
    text_path = text_dir + '/' + text_path
    text_id = re.sub('\.txt$', '', text_path.split('/')[-1])
    text_content = codecs.open(text_path, encoding='utf8').read()
    text = Text(text_id)
    text.tokenize(text_content)
    return text

if __name__ == '__main__':
    text_dir = sys.argv[1]
    default_base_fname = 'base.txt'
    collated = None
    # If base.txt is provided, use it.
    if default_base_fname in os.listdir(text_dir):
        collated = load_text(text_dir, default_base_fname)
    for text_fname in os.listdir(text_dir):
        if collated == None:
            # If base.txt is not provided, use first file in directory.
            collated = load_text(text_dir, text_fname)
        else:
            text = load_text(text_dir, text_fname)
        # Repeatedly collate using a common base text.
        collated = collate_text(collated, text)

    for token in collated.sequence:
        sys.stdout.write(token.base_word)
    print('=============')
    for token in collated.sequence:
        if token.base_word.strip() == '' or len(token._words) == 1:
            sys.stdout.write(token.base_word)
        else:
            sys.stdout.write('(')
            sys.stdout.write('|'.join(set([ w for w in token.iter_words() ])))
            sys.stdout.write(')')

