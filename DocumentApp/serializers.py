from rest_framework import serializers
from .models import Document

class DocumentUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ["id","file","filename","filetype","uploaded_at","extracted_text"]
        read_only_fields = ["id","uploaded_at","extracted_text"]

    def create(self, validated_data, **kwargs):
        user = kwargs.get("user", None)
        if user:
            validated_data["user"] = user

        if "file" in validated_data:
            f = validated_data["file"]
            validated_data["filename"] = getattr(f, "name", "")
            if not validated_data.get("filetype"):
                ext = validated_data["filename"].split(".")[-1].lower()
                mapping = {"pdf":"pdf", "docx":"docx", "txt":"txt", "pptx":"pptx", "csv":"csv", "jpg":"images", "jpeg":"images", "png":"images", "gif":"images"}
                validated_data["filetype"] = mapping.get(ext, "others")

        document = Document.objects.create(**validated_data)
        return document
