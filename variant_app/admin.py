from django.contrib import admin

from .models import Corpus, CollText, CollToken, Text, Token

admin.site.register(Corpus)
admin.site.register(CollText)
admin.site.register(CollToken)
admin.site.register(Text)
admin.site.register(Token)
