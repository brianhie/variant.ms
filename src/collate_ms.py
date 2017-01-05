# -*- coding: utf-8 -*-

import codecs
import collate as coll
import jellyfish as jf
import json
import os
import re
import string
import sys
import time
import uuid


class Text(coll.Coll):
    def __init__(self, text_id, corpus_id, content=u'', meta={}, base_text_id=''):
        super(Text, self).__init__([])
        self.text_id = text_id
        self.corpus_id = corpus_id
        self.meta = meta
        self.tokenize(content=content)
        self.base_text_id = base_text_id

    def load(self, text_path):
        content = codecs.open(text_path, encoding='utf8').read()
        self.tokenize(content=content)

    def tokenize(self, content=u''):
        if content == '':
            return
        seq = 0
        for a in re.split(r'(\s+)', content):
            if a.strip() == '':
                if self.text_id == '__COLL__':
                    self.sequence.append(CollToken(a, self.text_id,
                                                   self.corpus_id, seq,
                                                   self.base_text_id))
                else:
                    self.sequence.append(Token(a, self.text_id,
                                               self.corpus_id, seq))
                seq += 1
                continue
            for b in re.split(ur'([\.?!,:;\-–—―=…\}\]\)\"”’]+$|^[\{\[\(\"“‘]+)',
                              a, re.UNICODE):
                if b != '':
                    if self.text_id == '__COLL__':
                        self.sequence.append(CollToken(b, self.text_id,
                                                       self.corpus_id, seq,
                                                       self.base_text_id))
                    else:
                        self.sequence.append(Token(b, self.text_id,
                                                   self.corpus_id, seq))
                    seq += 1

    def ensure_dir(self, dname):
        if not os.path.exists(dname):
            os.makedirs(dname)

    def json_dump(self):
        corpus_dname = '../target/' + self.corpus_id
        self.ensure_dir(corpus_dname)
    
        # Write any meta data about text.
        text_dname = corpus_dname + '/' + self.text_id
        self.ensure_dir(text_dname)
        with open(text_dname + '/meta.json', 'w') as output_json:
            json.dump(self.meta, output_json)
    
        # Write tokens to their respective files.
        tokens_dname = text_dname + '/tokens'
        self.ensure_dir(tokens_dname)
        for token in self.sequence:
            token.json_dump()
    
    def add_token(self, token):
        self.sequence.append(token)

    def push_token(self, token):
        self.sequence.insert(0, token)


class Token(coll.CollElem):
    def __init__(self, word, text_id, corpus_id, seq, meta={}):
        self.word = word
        self.text_id = text_id
        self.corpus_id = corpus_id
        self.seq = seq
        self.meta = meta
        #self.id = '.'.join([str(f) for f in [ corpus_id, text_id, seq ]])

    def dict_dump(self):
        coll_token_meta = {}
        coll_token_meta['word'] = self.word
        coll_token_meta['text_id'] = self.text_id
        coll_token_meta['meta'] = self.meta
        return coll_token_meta

    def json_dump(self):
        token_meta = self.dict_dump()
        tokens_dname = ('../target/' + self.corpus_id +
                        '/' + self.text_id + '/tokens')
        with open(tokens_dname + '/' +
                  str(self.seq) + '.json', 'w') as output_json:
            json.dump(token_meta, output_json)


class CollToken(Token):
    def __init__(self, word, text_id, corpus_id, seq, base_text_id):
        self.base_text_id = base_text_id
        self._words = {}
        self._seqs = {}
        self.add(word, text_id, seq)
        super(CollToken, self).__init__(word, text_id, corpus_id, seq)

    def add(self, word, text_id, seqs):
        self._words[text_id] = word
        self._seqs[text_id] = seqs

    def add_seq(self, text_id, seq):
        self._seqs[text_id] += seq

    def get_word(self, text_id):
        return self._words[text_id]

    def get_seq(self, text_id):
        return self._seqs[text_id]

    def iter_words(self):
        for text_id in self._words:
            yield self._words[text_id], text_id, self._seqs[text_id]

    def dict_dump(self):
        coll_token_meta = {}
        tokens = []
        for word, text_id, seqs in self.iter_words():
            tokens.append({
                'word': word,
                'text_id': text_id,
                'seq': seqs
            })
            if text_id == self.base_text_id:
                coll_token_meta['base_word'] = word
                coll_token_meta['base_text_id'] = text_id
        coll_token_meta['tokens'] = tokens
        return coll_token_meta

    def json_dump(self):
        token_meta = self.dict_dump()
        tokens_dname = ('../target/' + self.corpus_id +
                        '/__COLL__/tokens')
        if not os.path.exists(tokens_dname):
            os.makedirs(tokens_dname)
        
        with open(tokens_dname + '/' +
                  str(self.seq) + '.json', 'w') as output_json:
            json.dump(token_meta, output_json)


def isspace(s):
    return s.strip() == ''

def ispunc(s):
    return s.rstrip(string.punctuation) == ''

def token_similarity(a, b):
    # Strings are a case insensitive match.
    # Match any whitespace to any whitespace.
    if a.word.lower().strip() == b.word.lower().strip():
        return 1.

    # Make it impossible for words to map to whitespace.
    if ((isspace(a.word) and not isspace(b.word)) or
        (not isspace(a.word) and isspace(b.word))):
        return -1.

    # Make it impossible for words to map to punctuation.
    if ispunc(a.word) and ispunc(b.word):
        return 0.9
    if ((ispunc(a.word) and not ispunc(b.word)) or
        (not ispunc(a.word) and ispunc(b.word))):
        return -1.

    # Strings sound alike (approximate phonetic match).
    if a.word.isalpha() and b.word.isalpha():
        if jf.metaphone(a.word) == jf.metaphone(b.word):
            return 0.9
        if jf.soundex(a.word) == jf.soundex(b.word):
            return 0.9
        if jf.nysiis(a.word) == jf.nysiis(b.word):
            return 0.9
        if jf.match_rating_codex(a.word) == jf.match_rating_codex(b.word):
            return 0.9

    # Use scaled Jaro-Winkler distance.
    return jf.jaro_winkler(a.word, b.word)

def collate_text(coll_text, text):
    new_coll_text = Text(coll_text.text_id, coll_text.corpus_id)
    insert_word = ''
    insert_seq = []
    for token_a, token_b, status in coll.collate(coll_text, text,
                                                 token_similarity):
        if status == 'match':
            assert(token_b.text_id == text.text_id)
            token_a.add(token_b.word + insert_word, token_b.text_id,
                        [ token_b.seq ])
            token_a.add_seq(text.text_id, insert_seq)
            new_coll_text.push_token(token_a)
            insert_word = ''
            insert_seq = []
        elif status == 'delete':
            token_a.add('' + insert_word, text.text_id, [])
            token_a.add_seq(text.text_id, insert_seq)
            new_coll_text.push_token(token_a)
            insert_word = ''
            insert_seq = []
        elif status == 'insert':
            assert(token_b.text_id == text.text_id)
            insert_word = token_b.word + insert_word
            insert_seq.append(token_b.seq)
        else:
            assert(False)
    if insert_word != '':
        first_word = new_coll_text.sequence[0].word
        new_coll_text.sequence[0].add(insert_word + first_word,
                                      text.text_id)
        new_coll_text.sequence[0].add_seq(text.text_id, insert_seq)
    return new_coll_text

def o_coll_print(collated):
    for token in collated.sequence:
        sys.stdout.write(token.word)
    print('=============')
    for token in collated.sequence:
        if token.word.strip() == '':
            sys.stdout.write(token.word)
        else:
            sys.stdout.write('(')
            sys.stdout.write('|'.join(set([ w[0] for w in token.iter_words() ])))
            sys.stdout.write(')')


if __name__ == '__main__':
    text_dir = sys.argv[1]
    default_base_fname = 'base.txt'
    listdir = os.listdir(text_dir)
    corpus_id = text_dir.rstrip('/').split('/')[-1]
    start = time.time()

    # If base.txt is provided, use it.
    coll_text = None
    if default_base_fname in listdir:
        text_id = re.sub('\.txt$', '', default_base_fname.split('/')[-1])
        coll_text = Text('__COLL__', corpus_id, base_text_id=text_id)
        coll_text.load(text_dir + '/' + default_base_fname)
        base_text = Text(text_id, corpus_id)
        base_text.load(text_dir + '/' + default_base_fname)
        base_text.json_dump()

    # Repeatedly collate all files in directory.
    for pos, text_fname in enumerate(listdir):
        text_id = re.sub('\.txt$', '', text_fname.split('/')[-1])
        if coll_text == None:
            # If base.txt is not provided, use first file in directory.
            coll_text = Text('__COLL__', corpus_id, base_text_id=text_id)
            coll_text.load(text_dir + '/' + text_fname)
            base_text = Text(text_id, corpus_id)
            base_text.load(text_dir + '/' + default_base_fname)
            base_text.json_dump()
            continue
        text = Text(text_id, corpus_id)
        text.load(text_dir + '/' + text_fname)
        text.json_dump()
        # Bulk of collation effort.
        coll_text = collate_text(coll_text, text)
        # Performance timer.
        end = time.time()
        sys.stdout.write('\r' + str(round(pos/float(len(listdir))*100, 1))
                         + '%, ' + str(round(end - start, 1)) + 's\033[K')
    sys.stdout.write('\r100%, ' + str(round(end - start, 1)) + 's\033[K\n')

    o_coll_print(coll_text)
    coll_text.json_dump()
