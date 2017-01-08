# -*- coding: utf-8 -*-

import codecs
import collate as coll
import jellyfish as jf
import json
import os
import pymongo
import re
import shutil
import string
import sys
import time
import uuid

_client = pymongo.MongoClient()
_db = _client.variant_db

class User:
    def __init__(self, user_id, **kwargs):
        user = _db.users.find_one({'user_id': user_id})
        if user == None:
            self.user_id = user_id
            self.meta = kwargs
            self._db_id = _db.users.insert_one(self.to_json_dict()).inserted_id
        else:
            self.from_json_dict(user)
            self._db_id = user['_id']
        
    def to_json_dict(self):
        meta = self.meta
        meta['user_id'] = self.user_id
        return meta

    def from_json_dict(self, meta):
        self.user_id = meta['user_id']
        self.meta = meta

class Corpus:
    def __init__(self, corpus_id, user_id, **kwargs):
        corpus = _db.corpuses.find_one({'corpus_id': corpus_id, 'user_id': user_id})
        if corpus == None:
            self.user_id = user_id
            self.corpus_id = corpus_id
            self.meta = kwargs
            self._db_id = _db.corpuses.insert_one(self.to_json_dict()).inserted_id
        else:
            self.from_json_dict(corpus)
            self._db_id = corpus['_id']

    def to_json_dict(self):
        meta = self.meta
        meta['user_id'] = self.user_id
        meta['corpus_id'] = self.corpus_id
        return meta

    def from_json_dict(self, meta):
        self.user_id = meta['user_id']
        self.corpus_id = meta['corpus_id']
        self.meta = meta

    def delete(self):
        _db.corpuses.delete_many({'corpus_id': self.corpus_id})
        _db.texts.delete_many({'corpus_id': self.corpus_id})
        _db.tokens.delete_many({'corpus_id': self.corpus_id})


class Text(coll.Coll):
    def __init__(self, text_id, corpus_id, user_id, **kwargs):
        super(Text, self).__init__()
        text = _db.texts.find_one({'text_id': text_id,
                                   'corpus_id': corpus_id,
                                   'user_id': user_id})
        if text == None:
            self.text_id = text_id
            self.corpus_id = corpus_id
            self.user_id = user_id
            if 'is_base' in kwargs:
                self.is_base = kwargs['is_base']
            else:
                self.is_base = False
            self.meta = kwargs
            self._db_id = _db.texts.insert_one(self.to_json_dict()).inserted_id
            if 'content' in kwargs:
                self._tokenize(kwargs['content'])
        else:
            self.from_json_dict(text)
            self._db_id = text['_id']
            self._load_tokens()

    def _load_tokens(self):
        tokens = []
        for token in _db.tokens.find({'text_db_id': self._db_id}).sort('seq'):
            self.sequence.append(Token(**token))

    def _tokenize(self, content):
        if content == '':
            return
        if isinstance(content, str):
            content = unicode(content, 'utf8')
        seq = 0
        for a in re.split(r'(\s+)', content):
            if a.strip() == '':
                token = Token(a, self.text_id, self.corpus_id, self.user_id, seq)
                token.ref_to_text(self._db_id)
                self.sequence.append(token)
                seq += 1
                continue
            for b in re.split(ur'([\.?!,:;\-–—―=…\}\]\)\"”’]+$|^[\{\[\(\"“‘]+)',
                              a, re.UNICODE):
                if b != '':
                    token = Token(b, self.text_id, self.corpus_id, self.user_id, seq)
                    token.ref_to_text(self._db_id)
                    self.sequence.append(token)
                    seq += 1

    def to_json_dict(self):
        meta = self.meta
        meta['user_id'] = self.user_id
        meta['corpus_id'] = self.corpus_id
        meta['text_id'] = self.text_id
        meta['is_base'] = self.is_base
        return meta

    def from_json_dict(self, meta):
        self.text_id = meta['text_id']
        self.corpus_id = meta['corpus_id']
        self.user_id = meta['user_id']
        self.is_base = meta['is_base']
        self.meta = meta

    def delete(self):
        # Do not delete base text.
        if self.is_base:
            return
        _db.texts.delete_many({'text_id': self.text_id})
        _db.tokens.delete_many({'text_id': self.text_id})


class Token(coll.CollElem):
    def __init__(self, word, text_id, corpus_id, user_id, seq, **kwargs):
        if '_id' in kwargs:
            token = _db.tokens.find_one({'_id': kwargs['_id']})
        else:
            token = _db.tokens.find_one({'text_id': text_id, 'corpus_id': corpus_id,
                                         'user_id': user_id, 'seq': seq})
        if token == None:
            self.word = word
            self.text_id = text_id
            self.corpus_id = corpus_id
            self.user_id = user_id
            self.seq = seq
            self.coll_token_id = None
            self.text_db_id = None
            self.meta = kwargs
        else:
            self.from_json_dict(token)
            self._db_id = token['_id']

    def ref_to_text(self, text_db_id):
        try:
            _db.tokens.find_one_and_update(
                {'_id': self._db_id}, {'$set': {'text_db_id': text_db_id}})
        except AttributeError:
            self.text_db_id = text_db_id

    def ref_to_coll(self, coll_token_id):
        try:
            _db.tokens.find_one_and_update(
                {'_id': self._db_id}, {'$set': {'coll_token_id': coll_token_id}})
        except:
            self.coll_token_id = coll_token_id

    def to_json_dict(self):
        meta = self.meta
        meta['word'] = self.word
        meta['text_id'] = self.text_id
        meta['corpus_id'] = self.corpus_id
        meta['user_id'] = self.user_id
        meta['seq'] = self.seq
        meta['coll_token_id'] = self.coll_token_id
        meta['text_db_id'] = self.text_db_id
        return meta

    def from_json_dict(self, meta):
        self.word = meta['word']
        self.text_id = meta['text_id']
        self.corpus_id = meta['corpus_id']
        self.user_id = meta['user_id']
        self.seq = meta['seq']
        self.coll_token_id = meta['coll_token_id']
        self.text_db_id = meta['text_db_id']
        self.meta = meta


class CollText(Text):
    def __init__(self, user_id, corpus_id, **kwargs):
        super(Text, self).__init__()

        self.text_id = '__COLL__'

        coll_text = _db.texts.find_one({'user_id': user_id,
                                        'corpus_id': corpus_id,
                                        'text_id': self.text_id})
        if coll_text == None or 'base_text' in kwargs:
            self._db_id = _db.texts.insert_one({}).inserted_id
            self.meta = kwargs
            self.load(kwargs['base_text']) # Coll text initially clones base text.
            del kwargs['base_text']
            _db.texts.find_one_and_update(
                {'_id': self._db_id}, {'$set': self.to_json_dict()})
        else:
            self.from_json_dict(coll_text)
            self._db_id = text['_id']
            self._load_tokens()

    def _load_tokens(self):
        for coll_token in _db.tokens.find({'text_db_id': self._db_id}).sort('seq'):
            self.sequence.append(CollToken(**coll_token))

    def load(self, text):
        self.user_id = text.user_id
        self.corpus_id = text.corpus_id
        self.base_text_id = text.text_id
        for seq, token in enumerate(text.sequence):
            coll_token = CollToken(token.word, self.text_id, self.corpus_id,
                                   self.user_id, seq, self.base_text_id)
            coll_token.text_db_id = self._db_id
            coll_token.ref_to_text(self._db_id)
            self.sequence.append(coll_token)
        _db.tokens.insert_many([ t.to_json_dict() for t in self.sequence ])
        self.sequence = []
        self._load_tokens()

    def from_json_dict(self, meta):
        self.meta = meta
        self.text_id = meta['text_id']
        self.corpus_id = meta['corpus_id']
        self.user_id = meta['user_id']
        self.base_text_id = meta[u'base_text_id']
        
    def to_json_dict(self):
        meta = self.meta
        meta['text_id'] = self.text_id
        meta['corpus_id'] = self.corpus_id
        meta['user_id'] = self.user_id
        meta['base_text_id'] = self.base_text_id
        return meta

    def collate(self, text):
        link_prev = []
        for coll_token, token, status in coll.collate(self, text,
                                                      token_similarity):
            if status == 'match':
                assert(token.text_id == text.text_id)
                # Link token to the coll token.
                token.ref_to_coll(coll_token._db_id)
                # Also link inserted tokens.
                for token in link_prev:
                    token.ref_to_coll(coll_token._db_id)
                link_prev = []
            elif status == 'delete':
                # No new tokens need to be linked.
                for token in link_prev:
                    token.ref_to_coll(coll_token._db_id)
                link_prev = []
                pass
            elif status == 'insert':
                # Inserted tokens map to first coll token.
                # (This loops iterates backwards through the texts.)
                link_prev.append(token)
            else:
                assert(False)
        for token in link_prev:
            token.ref_to_coll(coll_token._db_id)

        _db.tokens.insert_many([ t.to_json_dict() for t in text.sequence ])
        print([ t.to_json_dict() for t in text.sequence ])


class CollToken(Token):
    def __init__(self, word, text_id, corpus_id, user_id, seq,
                 base_text_id, **kwargs):
        if '_id' in kwargs:
            coll_token = _db.tokens.find_one({'_id': kwargs['_id']})
        else:
            coll_token = _db.tokens.find_one({'text_id': text_id,
                                              'corpus_id': corpus_id,
                                              'user_id':user_id,
                                              'seq': seq})
        if coll_token == None:
            self.word = word
            self.text_id = text_id
            self.corpus_id = corpus_id
            self.user_id = user_id
            self.seq = seq
            self.base_text_id = base_text_id
            self.meta = kwargs
            self.text_db_id = None
        else:
            self.from_json_dict(coll_token)
            self._db_id = coll_token['_id']

    def tokens(self):
#        print(self._db_id)
        for token in _db.tokens.find({'coll_token_id': self._db_id}).sort(
                [('text_id', pymongo.ASCENDING),
                 ('seq', pymongo.DESCENDING)]):
#            print(token)
            yield Token(**token)

    def words(self):
        for token in self.tokens():
            yield token.word

    def to_json_dict(self):
        meta = self.meta
        meta['word'] = self.word
        meta['text_id'] = self.text_id
        meta['corpus_id'] = self.corpus_id
        meta['user_id'] = self.user_id
        meta['seq'] = self.seq
        meta['base_text_id'] = self.base_text_id
        meta['text_db_id'] = self.text_db_id
        return meta

    def from_json_dict(self, meta):
        self.word = meta['word']
        self.text_id = meta['text_id']
        self.corpus_id = meta['corpus_id']
        self.user_id = meta['user_id']
        self.seq = meta['seq']
        self.base_text_id = meta['base_text_id']
        self.text_db_id = meta['text_db_id']
        self.meta = meta


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
    for coll_token in collated.sequence:
        sys.stdout.write(coll_token.word)
    print('=============')
    for coll_token in collated.sequence:
#        print([ a for a in coll_token.words()][0])
        variants = '|'.join(set([ w for w in coll_token.words() ]))
        if re.sub('\s+|\|', '', variants) == '':
            sys.stdout.write(coll_token.word)
        else:
            sys.stdout.write('(')
            sys.stdout.write(variants)
            sys.stdout.write(')')
    sys.stdout.write('\n')

def collate_corpus(corpus_dir, corpus_id, user_id,
                   default_base_fname='base.txt'):
    corpus = Corpus(corpus_id, user_id)
    corpus.delete()
    corpus = Corpus(corpus_id, user_id)
    listdir = os.listdir(corpus_dir)
    start = time.time()

    # If base.txt is provided, use it.
    print('Loading base...')
    coll_text = None
    if default_base_fname in listdir:
        text_id = re.sub('\.txt$', '', default_base_fname.split('/')[-1])
        base = Text(text_id, corpus_id, user_id,
                    content=open(corpus_dir + '/' + default_base_fname).read())
        print(time.time() - start)
        start = time.time()
        print('Loading coll...')
        coll_text = CollText(user_id, corpus_id, base_text=base)

    # Repeatedly collate all files in directory.
    print(time.time() - start)
    start = time.time()
    for pos, text_fname in enumerate(listdir):
        text_id = re.sub('\.txt$', '', text_fname.split('/')[-1])
        if coll_text == None:
            # If base.txt is not provided, use first file in directory.
            base = Text(text_id, corpus_id, user_id,
                        content=open(corpus_dir + '/' + default_base_fname).read())
            coll_text = CollText(user_id, corpus_id, base_text=base)
            continue
        print('Loading text...')
        text = Text(text_id, corpus_id, user_id,
                    content=open(corpus_dir + '/' + text_fname).read())
        print(time.time() - start)
        start = time.time()
        print('Collating...')
        coll_text.collate(text)
        print(time.time() - start)
        start = time.time()
        end = time.time()
#        sys.stdout.write('\r' + str(round(pos/float(len(listdir))*100, 1))
#                         + '%, ' + str(round(end - start, 1)) + 's\033[K')
#    sys.stdout.write('\r100%, ' + str(round(end - start, 1)) + 's\033[K\n')

    o_coll_print(coll_text)

def test_small():
    user_id = 'mr.ms'
    corpus_id = 'dummy corpus'

    # Create a corpus.
    corpus = Corpus(corpus_id, user_id)
#    corpus.delete()
#    corpus = Corpus(corpus_id, user_id)

    # Initialize a base text.
    text = Text('dummy base', corpus_id, user_id,
                content='Mary had a little lamb.', is_base=True)
    coll_text = CollText(corpus_id, user_id, base_text=text)
    coll_text.collate(text)

    # Add some dummy texts.
    text1 = Text('dummy text1', corpus_id, user_id,
                 content='Marry had 1 litle lambe.')
    coll_text.collate(text1)
    text2 = Text('dummy text2', corpus_id, user_id,
                 content='Marry had 2 litle lambes.')
    coll_text.collate(text2)
    text3 = Text('dummy text3', corpus_id, user_id,
                 content='Marry had 3 little lambs.')
    coll_text.collate(text3)

    # Print out the collation results.
    o_coll_print(coll_text)

    # Delete text 3.
    text3.delete()

    # See changes reflected in collated text.
    o_coll_print(coll_text)

    # Delete entire corpus.
#    corpus.delete()
    

if __name__ == '__main__':
    test_small()
    exit()
    corpus_dir = sys.argv[1]
    corpus_id = corpus_dir.rstrip('/').split('/')[-1]
    collate_corpus(corpus_dir, corpus_id, 'mr.ms')
