# -*- coding: utf-8 -*-

import codecs
import collate as coll
import jellyfish as jf
import json
import os
import re
import string
import sys
import uuid

class Text(coll.Coll):
    def __init__(self, text_id):
        super(Text, self).__init__([])
        self.text_id = text_id
        self.title = '(no title)'
        self.content = ''
        self.description = ''

    def tokenize(self, content=u''):
        self.content = content
        if content == '':
            return
        for a in re.split(r'(\s+)', content):
            if a.strip() == '':
                self.sequence.append(Token(a, self.text_id))
                continue
            for b in re.split(ur'([\.?!,:;\-–—―=…\}\]\)\"”’]+$|^[\{\[\(\"“‘]+)',
                              a, re.UNICODE):
                if b != '':
                    self.sequence.append(Token(b, self.text_id))

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

def isspace(s):
    return s.strip() == ''

def ispunc(s):
    return s.rstrip(string.punctuation) == ''

def token_similarity(a, b):
    # Strings are a case insensitive match.
    # Match any whitespace to any whitespace.
    if a.base_word.lower().strip() == b.base_word.lower().strip():
        return 1.

    # Make it near impossible for words to map to whitespace.
    if ((isspace(a.base_word) and not isspace(b.base_word)) or
        (not isspace(a.base_word) and isspace(b.base_word))):
        return -100000.

    # Make it near impossible for words to map to punctuation.
    if ispunc(a.base_word) and ispunc(b.base_word):
        return 0.9
    if ((ispunc(a.base_word) and not ispunc(b.base_word)) or
        (not ispunc(a.base_word) and ispunc(b.base_word))):
        return -100000.

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

    # Use scaled Jaro-Winkler distance.
    return (jf.jaro_winkler(a.base_word, b.base_word) * 2) - 1

def collate_text(master, text):
    new_master = Text('__COLL__')
    to_insert = ''
    for token_a, token_b, status in coll.collate(master, text,
                                                 token_similarity):
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
            to_insert = token_b.base_word + to_insert
        else:
            assert(False)
    if to_insert != '':
        first_word = new_master.sequence[0].base_word
        new_master.sequence[0].add(to_insert + first_word, text.text_id)
    return new_master

def load_text(text_dir, text_path):
    text_path = text_dir + '/' + text_path
    text_id = re.sub('\.txt$', '', text_path.split('/')[-1])
    text_content = codecs.open(text_path, encoding='utf8').read()
    text = Text(text_id)
    text.tokenize(text_content)
    return text

def o_coll_print(collated):
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

def o_coll_json(collated, name):
    coll_json = {}
    coll_json['title'] = 'Collated text'
    coll_json['text_id'] = str(uuid.uuid1())
    coll_json['description'] = ''
    coll_json['tokens'] = []
    for token in collated.sequence:
        words = [{
            'word': token.base_word,
            'text': token.base_text_id,
            'is_base': True
        }]
        for word, text_id in token.iter_word_texts():
            if text_id == token.base_text_id and word == token.base_word:
                continue
            words.append({
                'word': word,
                'text': text_id,
                'is_base': False
            })
        coll_json['tokens'].append(words)
    
    output_dname = '../target/' + name
    if not os.path.exists(output_dname):
        os.makedirs(output_dname)
    with open(output_dname + '/collated.json', 'w') as output_json:
        json.dump(coll_json, output_json, indent=4)

if __name__ == '__main__':
    text_dir = sys.argv[1]
    default_base_fname = 'base.txt'
    collated = None
    # If base.txt is provided, use it.
    import time
    start = time.time()
    if default_base_fname in os.listdir(text_dir):
        collated = load_text(text_dir, default_base_fname)
    for text_fname in os.listdir(text_dir):
        if collated == None:
            # If base.txt is not provided, use first file in directory.
            collated = load_text(text_dir, text_fname)
            continue
        else:
            text = load_text(text_dir, text_fname)
        end = time.time()
        print('Load text: ' + str(end - start))
        # Repeatedly collate using a common base text.
        collated = collate_text(collated, text)
        break
    exit()
    o_coll_print(collated)
    o_coll_json(collated, text_dir.rstrip('/').split('/')[-1])
