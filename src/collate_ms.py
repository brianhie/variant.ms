# -*- coding: utf-8 -*-

import codecs
import collate as coll
import jellyfish as jf
import json
import os
import re
import shutil
import string
import sys
import time
import uuid

class Corpus:
    def __init__(self, corpus_id, user_id):
        self.user_id = user_id
        self.corpus_id = corpus_id
        self.texts = []
        self._save_dname = get_path('', user_id, corpus_id)
        self._save_path = self._save_dname + '/meta.json'
        ensure_dir(self._save_dname)

    def add_text(self, text_id):
        self.texts.append(text_id)
        self.texts.sort()

    def remove_text(self, text_id):
        self.texts.remove(text_id)
        self.texts.sort()

    def savef(self):
        corpus_meta = {}
        corpus_meta['user_id'] = self.user_id
        corpus_meta['corpus_id'] = self.corpus_id
        corpus_meta['texts'] = self.texts
        with open(self._save_path, 'w') as output_json:
            json.dump(corpus_meta, output_json)

    def reloadf(self):
        with open(self._save_path, 'r') as json_file:
            corpus_meta = json.load(json_file)
        self.user_id = corpus_meta[u'user_id']
        self.corpus_id = corpus_meta[u'corpus_id']
        for text_id in corpus_meta[u'texts']:
            self.add_text(text_id)

    def deletef(self):
        for text_id in self.texts:
            text = Text(text_id, self.corpus_id, self.user_id)
            text.deletef()
        shutil.rmtree(self._save_dname)

class CollText(coll.Coll):
    def __init__(self):
        super(CollText, self).__init__([])
        # See load() method for bulk of initialization.

    def add_token(self, token):
        self.sequence.append(token)
        
    def push_token(self, token):
        self.sequence.insert(0, token)
        
    def load(self, text):
        self.user_id = text.user_id
        self.text_id = '__COLL__'
        self.corpus_id = text.corpus_id
        self.base_text_id = text.text_id
        for seq, token in enumerate(text.sequence):
            coll_token = CollToken(token.word, self.text_id, self.corpus_id,
                                   seq, self.base_text_id)
            coll_token.add(token.word, text.text_id, [seq])
            self.add_token(coll_token)
        self._save_dname = get_path('', self.user_id, self.corpus_id,
                                   self.text_id)
        self._save_path = self._save_dname + '/tokens.json'
        ensure_dir(self._save_dname)

    def json_to_coll_token(self, json_dict):
        word = json_dict[u'word']
        text_id = json_dict[u'text_id']
        corpus_id = json_dict[u'corpus_id']
        seq = json_dict[u'seq']
        base_text_id = json_dict[u'base_text_id']
        coll_token = CollToken(word, text_id, corpus_id, seq, base_text_id)
        for token in json_dict[u'tokens']:
            coll_token.add(token[u'word'], token[u'text_id'], token[u'seq'])
        return coll_token
        
    def reloadf(self, user_id, corpus_id):
        self._save_dname = get_path('', user_id, corpus_id, '__COLL__')
        self._save_path = self._save_dname + '/tokens.json'
        ensure_dir(self._save_dname)
        with open(self._save_path) as json_file:
            coll_token_meta = json.load(json_file)
        assert(coll_token_meta[u'user_id'] == user_id)
        assert(coll_token_meta[u'corpus_id'] == corpus_id)
        self.user_id = coll_token_meta[u'user_id']
        self.corpus_id = coll_token_meta[u'corpus_id']
        self.text_id = coll_token_meta[u'corpus_id']
        self.base_text_id = coll_token_meta[u'base_text_id']
        for t in coll_token_meta[u'coll_tokens']:
            token = self.json_to_coll_token(t)
            self.sequence.append(token)
        
    def savef(self):
        coll_text_meta = {}
        coll_text_meta['user_id'] = self.user_id
        coll_text_meta['corpus_id'] = self.corpus_id
        coll_text_meta['text_id'] = self.text_id
        coll_text_meta['base_text_id'] = self.base_text_id
        coll_text_meta['coll_tokens'] = []
        for token in self.sequence:
            coll_text_meta['coll_tokens'].append(token.to_json_dict())
        with open(self._save_path, 'w') as output_json:
            json.dump(coll_text_meta, output_json)

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
        coll_token_meta['seq'] = self.seq
        coll_token_meta['base_text_id'] = self.base_text_id
        coll_token_meta['tokens'] = []
        for word, text_id, seqs in self.iter_words():
            coll_token_meta['tokens'].append({
                'word': word,
                'text_id': text_id,
                'seq': seqs
            })
        return coll_token_meta


class Text(coll.Coll):
    def __init__(self, text_id, corpus_id, user_id, meta={}):
        super(Text, self).__init__([])
        self.text_id = text_id
        self.corpus_id = corpus_id
        self.user_id = user_id
        self.meta = meta
        self._save_dname = get_path('', self.user_id, self.corpus_id, self.text_id)
        ensure_dir(self._save_dname)
        
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

    def loads(self, text_string):
        self._tokenize(content=unicode(text_string, 'utf8'))

    def loadf(self, text_path):
        content = codecs.open(text_path, encoding='utf8').read()
        self._tokenize(content=content)

    def savef(self):
        meta_path = self._save_dname + '/meta.json'
        with open(meta_path, 'w') as output_json:
            json.dump(self.meta, output_json)
        coll_text_meta = {}
        coll_text_meta['user_id'] = self.user_id
        coll_text_meta['corpus_id'] = self.corpus_id
        coll_text_meta['text_id'] = self.text_id
        coll_text_meta['tokens'] = []
        for token in self.sequence:
            coll_text_meta['tokens'].append(token.to_json_dict())
        tokens_path = self._save_dname + '/tokens.json'
        with open(tokens_path, 'w') as output_json:
            json.dump(coll_text_meta, output_json)

    def deletef(self):
        shutil.rmtree(self._save_dname)


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

def get_path(fname, user_id='', corpus_id='', text_id=''):
    user_dname = os.path.expanduser('~')
    root_dname = '/'.join([user_dname, 'variant.ms', 'target'])
    if user_id == '':
        dname = root_dname
    elif corpus_id == '':
        dname = '/'.join([root_dname, user_id])
    elif text_id == '':
        dname = '/'.join([root_dname, user_id, corpus_id])
    else:
        dname = '/'.join([root_dname, user_id, corpus_id, text_id])
    return dname + '/' + fname

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

def create_corpus(user_id, corpus_id):
    corpus = Corpus(corpus_id, user_id)
    corpus.savef()
    return corpus

def delete_corpus(corpus):
    corpus.deletef()

def create_text(user_id, corpus_id, text_id, content, meta={}):
    text = Text(text_id, corpus_id, user_id, meta=meta)
    text.loads(content)
    text.savef()
    return text

def add_base(base, user_id, corpus_id):
    coll_text = CollText()
    coll_text.load(base)
    coll_text.savef()
    o_coll_print(coll_text)

    corpus = Corpus(corpus_id, user_id)
    corpus.add_text(base.text_id)
    corpus.savef()

    return coll_text

def add_text(text, user_id, corpus_id):
    coll_text = CollText()
    coll_text.reloadf(user_id, corpus_id)
    o_coll_print(coll_text)
    coll_text.collate(text)
    coll_text.savef()

    corpus = Corpus(corpus_id, user_id)
    corpus.reloadf()
    corpus.add_text(text.text_id)
    corpus.savef()
    return text

def delete_text(text):
    text_id = text.text_id
    user_id = text.user_id
    corpus_id = text.corpus_id
    text.deletef()

    corpus = Corpus(corpus_id, user_id)
    corpus.reloadf()
    corpus.remove_text(text_id)
    corpus.savef()
    

def collate_corpus(corpus_dir, corpus_id, user_id,
                   default_base_fname='base.txt'):
    listdir = os.listdir(corpus_dir)
    start = time.time()
    # If base.txt is provided, use it.
    coll_text = None
    if default_base_fname in listdir:
        text_id = re.sub('\.txt$', '', default_base_fname.split('/')[-1])
        base = Text(text_id, corpus_id, user_id)
        base.loadf(corpus_dir + '/' + default_base_fname)
        coll_text = add_base(base, user_id, corpus_id)
    # Repeatedly collate all files in directory.
    for pos, text_fname in enumerate(listdir):
        text_id = re.sub('\.txt$', '', text_fname.split('/')[-1])
        if coll_text == None:
            # If base.txt is not provided, use first file in directory.
            base = Text(text_id, corpus_id, user_id)
            base.loadf(corpus_dir + '/' + default_base_fname)
            coll_text = add_base(base, user_id, corpus_id)
            continue
        text = Text(text_id, corpus_id, user_id)
        text.loadf(corpus_dir + '/' + text_fname)
        text.savef()
        coll_text.collate(text)
        end = time.time()
        sys.stdout.write('\r' + str(round(pos/float(len(listdir))*100, 1))
                         + '%, ' + str(round(end - start, 1)) + 's\033[K')
    sys.stdout.write('\r100%, ' + str(round(end - start, 1)) + 's\033[K\n')

    o_coll_print(coll_text)
    coll_text.savef()

def test():
    corpus = create_corpus('mr.ms', 'dummy corpus')
    text = create_text('mr.ms', 'dummy corpus', 'dummy base',
                       'Mary had a little lamb.')
    add_base(text, 'mr.ms', 'dummy corpus')
    text = create_text('mr.ms', 'dummy corpus', 'dummy text',
                       'Marry had 1 litle lambe.')
    add_text(text, 'mr.ms', 'dummy corpus')
    text = create_text('mr.ms', 'dummy corpus', 'dummy text1',
                       'Marry had 1 litle lambe.')
    add_text(text, 'mr.ms', 'dummy corpus')
    text = create_text('mr.ms', 'dummy corpus', 'dummy text2',
                       'Marry had 1 litle lambe.')
    add_text(text, 'mr.ms', 'dummy corpus')
    delete_text(text)

if __name__ == '__main__':
    #test()
    corpus_dir = sys.argv[1]
    corpus_id = corpus_dir.rstrip('/').split('/')[-1]
    collate_corpus(corpus_dir, 'mr.s', corpus_id)
