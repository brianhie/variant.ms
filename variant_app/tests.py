from django.test import TestCase
from django.db import transaction
import os
import re
import sys
import time

from .controllers import create_text
from .models import Corpus, Text, Token, CollText, CollToken

class VariantAppTests(TestCase):
    def _o_coll_print(self, collated):
        for coll_token in collated.tokens():
            sys.stdout.write(coll_token.word)
        print('=============')
        for coll_token in collated.tokens():
            variants = '|'.join(set([ w.word for w in coll_token.tokens() ]))
            if re.sub('\s+|\|', '', variants) == '':
                sys.stdout.write(coll_token.word)
            else:
                sys.stdout.write('(')
                sys.stdout.write(variants)
                sys.stdout.write(')')
        sys.stdout.write('\n')

    # Ensure tokenization algorithm does not lose data.
    def test_word_loss(self):
        corpus = Corpus(corpus_name='test word loss')
        corpus.save()
        content = 'Mary had a (little) lamb.'
        text = create_text(corpus, 'base text', content)
        text_content = ''.join([ t.word for t in text.tokens() ])
        assert(content == text_content)

    # Ensure that collation algorithm is working at a basic level.
    def test_collation(self):
        corpus = Corpus(corpus_name='test collation')
        corpus.save()

        content = 'Mary had a little lamb.'
        base = create_text(corpus, 'base text', content)
        content = 'Marry had 1 litle lambe.'
        text1 = create_text(corpus, 'text 1', content)

        coll_text = CollText.objects.get(corpus=corpus)
        for coll_token in coll_text.tokens():
            for token in coll_token.tokens():
                if token.text == text1:
                    if token.seq == 0:
                        assert(token.word == 'Marry')
                    elif token.seq == 4:
                        assert(token.word == '1')
                    elif token.seq == 6:
                        assert(token.word == 'litle')
                if token.seq == 9:
                    assert(token.word == '.')

    # Ensure deleted texts do not show up in collated text.
    def test_delete_text(self):
        # Create a corpus.
        corpus = Corpus(corpus_name='test delete text')
        corpus.save()
    
        # Initialize a base text.
        content = 'Mary had a little lamb.'
        create_text(corpus, 'base text', content)
    
        # Add some dummy texts.
        content = 'Marry had 1 litle lambe.'
        text1 = create_text(corpus, 'text 1', content)
        content = 'Mary had 2 cute little lambs.'
        text2 = create_text(corpus, 'text 2', content)
        content = 'Mary hade 3 little lambes!'
        text3 = create_text(corpus, 'text 3', content)
    
        # Print out the collation results.
        coll_text = CollText.objects.get(corpus=corpus)
        self._o_coll_print(coll_text)
    
        # Delete text 3.
        text3.delete()

        # See changes reflected in collated text.
        for coll_token in coll_text.tokens():
            for token in coll_token.tokens():
                assert(token.word != '3')
                assert(token.word != 'lambes')
        coll_text = CollText.objects.get(corpus=corpus)
        self._o_coll_print(coll_text)
    

    def test_HSDeath(self):
        corpus_dir = os.path.expanduser('~/variant.ms/variant_app/data/Donne_HSDeath')
        self.full_corpus(corpus_dir)

    def test_Sat3(self):
        corpus_dir = os.path.expanduser('~/variant.ms/variant_app/data/Donne_Sat3')
        self.full_corpus(corpus_dir)
        
    def full_corpus(self, corpus_dir):
        corpus_id = 'Donne_HSDeath'
        default_base_fname = 'base.txt'

        start = time.time()
        corpus = Corpus(corpus_name=corpus_id)
        corpus.save()
        listdir = os.listdir(corpus_dir)
    
        # If base.txt is provided, use it.
        base_provided = default_base_fname in listdir
        if base_provided:
            base_text_id = re.sub('\.txt$', '', default_base_fname.split('/')[-1])
            content = open(corpus_dir + '/' + default_base_fname).read()
            create_text(corpus, base_text_id, content, debug=True)
    
        # Repeatedly collate all files in directory.
        for pos, text_fname in enumerate(listdir):
            text_id = re.sub('\.txt$', '', text_fname.split('/')[-1])
            if not base_provided:
                # If base.txt is not provided, use first file in directory.
                content = open(corpus_dir + '/' + default_base_fname).read()
                create_text(corpus, text_id, content, debug=True)
                continue
            elif text_id == base_text_id:
                continue
            content = open(corpus_dir + '/' + text_fname).read()
            create_text(corpus, text_id, content, debug=True)
            end = time.time()
            sys.stdout.write('\r' + str(round(pos/float(len(listdir))*100, 1))
                             + '%, ' + str(round(end - start, 1)) + 's\033[K')
        sys.stdout.write('\r100%, ' + str(round(end - start, 1)) + 's\033[K\n')
    
        coll_text = CollText.objects.get(corpus__id=corpus.id)
        self._o_coll_print(coll_text)

