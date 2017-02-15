from django.contrib import admin

from .models import Corpus, CollText, CollToken, Text, Token, Block, Profile, Query

admin.site.register(Corpus)
admin.site.register(CollText)
admin.site.register(CollToken)
admin.site.register(Text)
admin.site.register(Token)
admin.site.register(Block)
admin.site.register(Profile)
admin.site.register(Query)
