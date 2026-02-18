from django.contrib import admin
from .models import Document, Chunk, QueryHistory

admin.site.register(Document)
admin.site.register(Chunk)
admin.site.register(QueryHistory)
