from django.db import models
from django.conf import settings

class Document(models.Model):
    FileType = [
        ("pdf","PDF"),
        ("docx","DOCX"),
        ("txt","TXT"),
        ("pptx","PPTX"),
        ("csv","CSV"),
        ("images","Images"),
        ("others","Others"),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    file = models.FileField(upload_to='documents/')
    filename = models.CharField(max_length=512, blank=True, null=True)
    filetype = models.CharField(max_length=16, choices=FileType, default="others")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    extracted_text = models.TextField(blank=True, null=True)
    metadata = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"Document {self.id} - {self.filename}"

class Chunk(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks')
    chunk_index = models.PositiveIntegerField()
    text = models.TextField()
    chroma_id = models.CharField(max_length=256, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("document","chunk_index")
        ordering = ("chunk_index",)

    def __str__(self):
        return f"Chunk {self.chunk_index} of Document {self.document.id}"

class QueryHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    query_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    top_ids = models.TextField(blank=True, null=True)
    answer = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"QueryHistory {self.created_at} for '{self.query_text[:50]}'"
