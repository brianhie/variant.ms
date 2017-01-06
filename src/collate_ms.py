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

class CollText(coll.Coll):
    def __init__(self):
        super(CollText, self).__init__([])
        # See load() method for bulk of initialization.

    def add_token(self, token):
        self.sequence.append(token)
        
    def push_token(self, token):
        self.sequence.insert(0, token)
        
    def load(self, text):
        self.text_id = '__COLL__'
        self.corpus_id = text.corpus_id
        self.base_text_id = text.text_id
        for seq, token in enumerate(text.sequence):
            coll_tok = CollToken(token.word, self.text_id, self.corpus_id,
                                 seq, self.base_text_id)
            self.add_token(coll_tok)
        # Directory info.
        self.corpus_dname = '../target/' + self.corpus_id
        ensure_dir(self.corpus_dname)
        self.text_dname = self.corpus_dname + '/' + self.text_id
        ensure_dir(self.text_dname)
        self.tokens_dname = self.text_dname + '/tokens'
        ensure_dir(self.tokens_dname)
        
    def reload(self, corpus_id):
        self.text_id = '__COLL__'
        self.corpus_id = corpus_id
        self.tokens_dname = '../target/' + corpus_id + '/__COLL__/tokens'
        for seq, token_fname in enumerate(os.listdir(self.tokens_dname)):
            with open(self.tokens_dname + '/' + token_fname) as json_file:
                coll_token_meta = json.load(json_file)
            assert(coll_token_meta[u'text_id'] == self.text_id)
            assert(coll_token_meta[u'corpus_id'] == self.corpus_id)
            if seq == 0:
                self.base_text_id = coll_token_meta[u'base_text_id']
            else:
                assert(coll_token_meta[u'base_text_id'] == self.base_text_id)
            coll_tok = CollToken(coll_token_meta[u'word'],
                                 self.text_id, self.corpus_id, seq,
                                 self.base_text_id)
            for token in coll_token_meta[u'tokens']:
                coll_tok.add(token['word'], token['text_id'],
                             token['seq'])
            self.sequence.append(coll_tok)
        
    def save(self):
        tokens = []
        for token in self.sequence:
            tokens.append(token.to_json_dict())
        with open(self.text_dname + '/tokens.json', 'w') as output_json:
            json.dump({'tokens': tokens}, output_json)

    def collate(self, text):
        insert_word = ''
        insert_seq = []
        for token_a, token_b, status in coll.collate(self, text,
                                                     token_similarity):
            if status == 'match':
                assert(token_b.text_id == text.text_id)
                token_a.add(token_b.word + insert_word, token_b.text_id,
                            [ token_b.seq ])
                token_a.add_seq(text.text_id, insert_seq)
                insert_word = ''
                insert_seq = []
            elif status == 'delete':
                token_a.add('' + insert_word, text.text_id, [])
                token_a.add_seq(text.text_id, insert_seq)
                insert_word = ''
                insert_seq = []
            elif status == 'insert':
                assert(token_b.text_id == text.text_id)
                insert_word = token_b.word + insert_word
                insert_seq.append(token_b.seq)
            else:
                assert(False)
        if insert_word != '':
            first_word = self.sequence[0].word
            self.sequence[0].add(insert_word + first_word,
                                 text.text_id)
            self.sequence[0].add_seq(text.text_id, insert_seq)


class CollToken(coll.CollElem):
    def __init__(self, word, text_id, corpus_id, seq, base_text_id):
        super(CollToken, self).__init__()
        self.word = word
        self.text_id = text_id
        self.corpus_id = corpus_id
        self.seq = seq
        self.base_text_id = base_text_id
        self._words = {}
        self._seqs = {}
        self.add(word, text_id, seq)

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

    def to_json_dict(self):
        coll_token_meta = {}
        coll_token_meta['word'] = self.word
        coll_token_meta['text_id'] = self.text_id
        coll_token_meta['corpus_id'] = self.corpus_id
        coll_token_meta['base_text_id'] = self.base_text_id
        tokens = []
        for word, text_id, seqs in self.iter_words():
            tokens.append({
                'word': word,
                'text_id': text_id,
                'seq': seqs
            })
        coll_token_meta['tokens'] = tokens
        return coll_token_meta


class Text(coll.Coll):
    def __init__(self, text_id, corpus_id, meta={}):
        super(Text, self).__init__([])
        self.text_id = text_id
        self.corpus_id = corpus_id
        self.meta = meta
        
        self.corpus_dname = '../target/' + self.corpus_id
        ensure_dir(self.corpus_dname)
        self.text_dname = self.corpus_dname + '/' + self.text_id
        ensure_dir(self.text_dname)
        self.tokens_dname = self.text_dname + '/tokens'
        ensure_dir(self.tokens_dname)
        
    def _tokenize(self, content=u''):
        if content == '':
            return
        seq = 0
        for a in re.split(r'(\s+)', content):
            if a.strip() == '':
                self.sequence.append(Token(a, self.text_id,
                                           self.corpus_id, seq))
                seq += 1
                continue
            for b in re.split(ur'([\.?!,:;\-–—―=…\}\]\)\"”’]+$|^[\{\[\(\"“‘]+)',
                              a, re.UNICODE):
                if b != '':
                    self.sequence.append(Token(b, self.text_id,
                                               self.corpus_id, seq))
                    seq += 1

    def load(self, text_path):
        content = codecs.open(text_path, encoding='utf8').read()
        self._tokenize(content=content)

    def save(self):
        with open(self.text_dname + '/meta.json', 'w') as output_json:
            json.dump(self.meta, output_json)
        tokens = []
        for token in self.sequence:
            tokens.append(token.to_json_dict())
        with open(self.text_dname + '/tokens.json', 'w') as output_json:
            json.dump({'tokens': tokens}, output_json)


class Token(coll.CollElem):
    def __init__(self, word, text_id, corpus_id, seq, meta={}):
        self.word = word
        self.text_id = text_id
        self.corpus_id = corpus_id
        self.seq = seq
        self.meta = meta

    def to_json_dict(self):
        coll_token_meta = {}
        coll_token_meta['word'] = self.word
        coll_token_meta['text_id'] = self.text_id
        coll_token_meta['corpus_id'] = self.corpus_id
        coll_token_meta['meta'] = self.meta
        return coll_token_meta


def ensure_dir(dname):
    if not os.path.exists(dname):
        os.makedirs(dname)

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

def o_coll_print(collated):
    for token in collated.sequence:
        sys.stdout.write(token.word)
    print('=============')
    for token in collated.sequence:
        variants = '|'.join(set([ w[0] for w in token.iter_words() ]))
        if re.sub('\s+|\|', '', variants) == '':
            sys.stdout.write(token.word)
        else:
            sys.stdout.write('(')
            sys.stdout.write(variants)
            sys.stdout.write(')')
    sys.stdout.write('\n')

def create_base(base_path, corpus_id):
    # Parse the base text.
    text_id = re.sub('\.txt$', '', base_path.split('/')[-1])
    base_text = Text(text_id, corpus_id)
    base_text.load(base_path)
    base_text.save()

    # Generate the special collated text.
    coll_text = CollText()
    coll_text.load(base_text)
    coll_text.save()
    return coll_text

def add_text(text_path, corpus_id):
    # Reload the special collated text.
    coll_text = CollText()
    coll_text.reload(corpus_id)
    # Load the text and save it.
    text_id = re.sub('\.txt$', '', text_path.split('/')[-1])
    text = Text(text_id, corpus_id)
    text.load(text_path)
    text.save()
    # Perform the collation and update.
    coll_text.collate(text)
    coll_text.save()
    return text

def collate_corpus(corpus_dir, corpus_id,
                   default_base_fname='base.txt'):
    listdir = os.listdir(corpus_dir)
    start = time.time()
    # If base.txt is provided, use it.
    coll_text = None
    if default_base_fname in listdir:
        coll_text = create_base(corpus_dir + '/' + default_base_fname,
                                corpus_id)
    # Repeatedly collate all files in directory.
    for pos, text_fname in enumerate(listdir):
        text_id = re.sub('\.txt$', '', text_fname.split('/')[-1])
        if coll_text == None:
            # If base.txt is not provided, use first file in directory.
            coll_text = create_base(corpus_dir + '/' + text_fname,
                                    corpus_id)
            continue
        text = Text(text_id, corpus_id)
        text.load(corpus_dir + '/' + text_fname)
        text.save()
        coll_text.collate(text)
        end = time.time()
        sys.stdout.write('\r' + str(round(pos/float(len(listdir))*100, 1))
                         + '%, ' + str(round(end - start, 1)) + 's\033[K')
    sys.stdout.write('\r100%, ' + str(round(end - start, 1)) + 's\033[K\n')

    o_coll_print(coll_text)
    coll_text.save()


if __name__ == '__main__':
    corpus_dir = sys.argv[1]
    corpus_id = corpus_dir.rstrip('/').split('/')[-1]
    collate_corpus(corpus_dir, corpus_id)
