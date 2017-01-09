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
    
    @transaction.atomic
    def test_small(self):
        corpus_id = 'dummy corpus'
    
        # Create a corpus.
        corpus = Corpus(corpus_name=corpus_id)
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
        coll_text = CollText.objects.get(corpus__id=corpus.id)
        self._o_coll_print(coll_text)
    
        # Delete text 3.
        text3.delete()
    
        # See changes reflected in collated text.
        coll_text = CollText.objects.get(corpus__id=corpus.id)
        self._o_coll_print(coll_text)
    
        # Delete entire corpus.
        corpus.delete()

    def test_HSDeath(self):
        corpus_dir = os.path.expanduser('./data/Donne_HSDeath')
        self.full_corpus(corpus_dir)

    def test_Sat3(self):
        corpus_dir = os.path.expanduser('./data/Donne_Sat3')
        #self.full_corpus(corpus_dir)
        
    @transaction.atomic
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
            create_text(corpus, base_text_id, content)
    
        # Repeatedly collate all files in directory.
        for pos, text_fname in enumerate(listdir):
            text_id = re.sub('\.txt$', '', text_fname.split('/')[-1])
            if not base_provided:
                # If base.txt is not provided, use first file in directory.
                content = open(corpus_dir + '/' + default_base_fname).read()
                create_text(corpus, text_id, content)
                continue
            elif text_id == base_text_id:
                continue
            content = open(corpus_dir + '/' + text_fname).read()
            create_text(corpus, text_id, content)
            end = time.time()
            sys.stdout.write('\r' + str(round(pos/float(len(listdir))*100, 1))
                             + '%, ' + str(round(end - start, 1)) + 's\033[K')
        sys.stdout.write('\r100%, ' + str(round(end - start, 1)) + 's\033[K\n')
    
        coll_text = CollText.objects.get(corpus__id=corpus.id)
        self._o_coll_print(coll_text)

