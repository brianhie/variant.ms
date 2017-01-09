from django.db import models
from django.utils.encoding import python_2_unicode_compatible

@python_2_unicode_compatible
class Corpus(models.Model):
    corpus_name = models.CharField(max_length=100)

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
    seq = models.IntegerField(default=-1)

    def __str__(self):
        return self.coll_text.text_name + '_' + str(self.seq)

    def tokens(self):
        try:
            tokens = Token.objects.filter(coll_token__id=self.id).order_by('text__text_name', 'seq')
        except Token.DoesNotExist:
            tokens = []
        return tokens


@python_2_unicode_compatible
class Text(models.Model):
    text_name = models.CharField(max_length=100)
    corpus = models.ForeignKey(Corpus, on_delete=models.CASCADE)
    is_base = models.BooleanField(default=False)

    def __str__(self):
        return self.text_name

    def tokens(self):
        try:
            tokens = Token.objects.filter(text__id=self.id).order_by('seq')
        except Token.DoesNotExist:
            tokens = []
        return tokens


@python_2_unicode_compatible
class Token(models.Model):
    corpus = models.ForeignKey(Corpus, on_delete=models.CASCADE, default=None)
    text = models.ForeignKey(Text, on_delete=models.CASCADE, default=None)
    coll_token = models.ForeignKey(CollToken, on_delete=models.CASCADE, default=None)
    word = models.TextField(default='')
    seq = models.IntegerField(default=-1)
    is_base = models.BooleanField(default=False)

    def __str__(self):
        return self.text.text_name + '_' + str(self.seq)
