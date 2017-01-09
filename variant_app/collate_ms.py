from django.db import transaction
from controllers import create_text
from models import *

def o_coll_print(collated):
    for coll_token in collated.tokens():
        sys.stdout.write(coll_token.word)
    print('=============')
    for coll_token in collated.tokens():
#        print([ a for a in coll_token.words()][0])
        variants = '|'.join(set([ w.word for w in coll_token.token() ]))
        if re.sub('\s+|\|', '', variants) == '':
            sys.stdout.write(coll_token.word)
        else:
            sys.stdout.write('(')
            sys.stdout.write(variants)
            sys.stdout.write(')')
    sys.stdout.write('\n')

@transaction.atomic
def collate_corpus(corpus_dir, corpus_id, user_id,
                   default_base_fname='base.txt'):
    corpus = Corpus(corpus_name=corpus_id)
#    corpus.delete()
#    corpus = Corpus(corpus_id)
    listdir = os.listdir(corpus_dir)
    start = time.time()

    # If base.txt is provided, use it.
    print('Loading base...')
    coll_text = None
    if default_base_fname in listdir:
        text_id = re.sub('\.txt$', '', default_base_fname.split('/')[-1])
        base = Text(text_name=text_id, corpus=corpus, is_base=True)
        content = open(corpus_dir + '/' + default_base_fname)
        create_text(corpus, text_id, content)
        print(time.time() - start)
        start = time.time()

    # Repeatedly collate all files in directory.
    for pos, text_fname in enumerate(listdir):
        text_id = re.sub('\.txt$', '', text_fname.split('/')[-1])
        if coll_text == None:
            # If base.txt is not provided, use first file in directory.
            base = Text(text_name=text_id, corpus=corpus, is_base=True)
            content = open(corpus_dir + '/' + default_base_fname)
            create_text(corpus, text_id, content)
            continue
        elif text_id == base.text_id:
            continue
        print('Loading text and collating...')
        text = Text(text_name=text_id, corpus=corpus)
        content = open(corpus_dir + '/' + text_fname)
        create_text(corpus, text_id, content)
        print(time.time() - start)
        start = time.time()
        end = time.time()
#        sys.stdout.write('\r' + str(round(pos/float(len(listdir))*100, 1))
#                         + '%, ' + str(round(end - start, 1)) + 's\033[K')
#    sys.stdout.write('\r100%, ' + str(round(end - start, 1)) + 's\033[K\n')

    o_coll_print(coll_text)

@transaction.atomic
def test_small():
    user_id = 'mrms'
    corpus_id = 'dummy corpus'

    # Create a corpus.
    corpus = Corpus(corpus_name=corpus_id)

    # Initialize a base text.
    text = Text(text_name='base text', corpus=corpus, is_base=True)
    content = 'Mary had a little lamb.'
    create_text(corpus, text_id, content)

    # Add some dummy texts.
    text1 = Text(text_name='text 1', corpus=corpus)
    content = 'Marry had 1 litle lambe.'
    create_text(corpus, text_id, content)
    text2 = Text(text_name='text 2', corpus=corpus)
    content = 'Mary had 2 cute little lambs.'
    create_text(corpus, text_id, content)
    text3 = Text(text_name='text 3', corpus=corpus)
    content = 'Mary hade 3 little lambes!'
    create_text(corpus, text_id, content)

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
    collate_corpus(corpus_dir, corpus_id, 'mrms')
