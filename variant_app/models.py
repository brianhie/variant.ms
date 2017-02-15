from django.contrib.auth.models import User
from django.contrib.postgres.search import SearchVectorField
from django.db import models
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class Corpus(models.Model):
    user = models.ForeignKey(User, null=True, default=None, on_delete=models.CASCADE)
    corpus_name = models.CharField(max_length=100)
    author = models.CharField(max_length=100, blank=True)
    description = models.TextField(default='', blank=True)
    preview = models.CharField(max_length=2000, default='')

    is_public = models.BooleanField(default=True)
    n_favorites = models.IntegerField(default=0)
    n_views = models.IntegerField(default=0)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.corpus_name


@python_2_unicode_compatible
class CollText(models.Model):
    text_name = models.CharField(max_length=10, default='__COLL__')
    corpus = models.ForeignKey(Corpus, on_delete=models.CASCADE)

    def __str__(self):
        return self.text_name

    def tokens(self):
        try:
            tokens = CollToken.objects.filter(coll_text__id=self.id).order_by('seq')
        except CollToken.DoesNotExist:
            tokens = []
        return tokens


@python_2_unicode_compatible    
class CollToken(models.Model):
    corpus = models.ForeignKey(Corpus, on_delete=models.CASCADE, default=None)
    coll_text = models.ForeignKey(CollText, on_delete=models.CASCADE, default=None)
    word = models.TextField(default='')
    seq = models.IntegerField(default=-2)
    variability = models.FloatField(default=0.)
    is_hidden = models.BooleanField(default=False)

    def __str__(self):
        return self.coll_text.text_name + '_' + str(self.seq)

    def tokens(self):
        try:
            tokens = Token.objects.filter(coll_token_seq=self.seq, corpus=self.corpus).order_by('text__text_name', 'seq')
        except Token.DoesNotExist:
            tokens = []
        return tokens


@python_2_unicode_compatible
class Text(models.Model):
    text_name = models.CharField(max_length=100)
    corpus = models.ForeignKey(Corpus, on_delete=models.CASCADE)
    is_base = models.BooleanField(default=False)
    date = models.DateField(null=True, default=None)
    date_end = models.DateField(null=True, default=None)
    editor = models.CharField(max_length=100, blank=True)
    description = models.TextField(default='')

    def __str__(self):
        return self.text_name

    def tokens(self):
        try:
            tokens = Token.objects.filter(text__id=self.id).order_by('seq')
        except Token.DoesNotExist:
            tokens = []
        return tokens

    def blocks(self):
        try:
            blocks = Block.objects.filter(text__id=self.id).order_by('token_start__seq')
        except Block.DoesNotExist:
            blocks = []
        return blocks


@python_2_unicode_compatible
class Token(models.Model):
    corpus = models.ForeignKey(Corpus, on_delete=models.CASCADE, default=None)
    text = models.ForeignKey(Text, on_delete=models.CASCADE, default=None)
    coll_token_seq = models.IntegerField(default=-1)
    word = models.TextField(default='')
    seq = models.IntegerField(default=-1)
    is_base = models.BooleanField(default=False)
    variability = models.FloatField(default=0.)

    def __str__(self):
        return self.text.text_name + '_' + str(self.seq)


@python_2_unicode_compatible
class Block(models.Model):
    corpus = models.ForeignKey(Corpus, on_delete=models.CASCADE)
    text = models.ForeignKey(Text, on_delete=models.CASCADE)
    token_start = models.ForeignKey(Token,
                                    related_name='%(app_label)s_%(class)s_start')
    token_end = models.ForeignKey(Token, default=None, blank=True,
                                  related_name='%(app_label)s_%(class)s_end')
    coll_token_start = models.ForeignKey(CollToken,
                                         related_name='%(app_label)s_%(class)s_start')
    coll_token_end = models.ForeignKey(CollToken, default=None, blank=True,
                                       related_name='%(app_label)s_%(class)s_end')

    def __str__(self):
        return (self.text.text_name + '_' +
                str(self.token_start) + ':' + str(self.token_end) + '->' +
                str(self.coll_token_start) + ':' + str(self.coll_token_end))

@python_2_unicode_compatible
class Profile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    favorites = models.ManyToManyField(Corpus)

    def __str__(self):
        return self.user.username

@python_2_unicode_compatible
class Query(models.Model):
    query = models.CharField(max_length=100)
    n_queries = models.IntegerField(default=0)

    def __str__(self):
        return self.query
