from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from .serializers import DocumentUploadSerializer
from .ingest_pipeline import ingest_document
from .ollama_embedding import embed_query
from .ollama_llm import generate_response
from .models import Document, QueryHistory
import chromadb
from django.conf import settings
import logging

logger = logging.getLogger(__name__)
client = chromadb.PersistentClient(path=str(settings.CHROMA_PERSIST_DIRECTORY))
collection = client.get_or_create_collection(name=str(settings.CHROMA_COLLECTION_NAME))

def index(request):
    return render(request, 'index.html', {})

class DocumentUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        user = request.user if request.user.is_authenticated else None
        serializer = DocumentUploadSerializer(data=request.data)
        if serializer.is_valid():
            doc = serializer.save(user=user)
            try:
                chunk_count = ingest_document(doc.id)
            except Exception as e:
                logger.exception("Ingest failed")
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            data = dict(DocumentUploadSerializer(doc).data)
            data["chunk_count"] = chunk_count
            return Response(data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SearchView(APIView):
    def post(self, request):
        query = (request.data.get("query") or "").strip()
        if not query:
            return Response({"error":"Query is required"}, status=status.HTTP_400_BAD_REQUEST)
        user = request.user if request.user.is_authenticated else None

        try:
            qvec = embed_query(query)
        except Exception:
            logger.exception("Embedding failed")
            return Response({"error":"Failed to embed query"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            results = collection.query(query_embeddings=[qvec], n_results=5)
        except Exception:
            logger.exception("Chroma query failed")
            return Response({"error":"Failed to query documents"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Safe unpacking: results['documents'] can be nested
        documents = results.get("documents") or []
        metadatas = results.get("metadatas") or []
        ids = results.get("ids") or []

        docs = documents[0] if documents and isinstance(documents[0], list) else (documents if documents and isinstance(documents, list) and isinstance(documents[0], str) else [])
        metas = metadatas[0] if metadatas and isinstance(metadatas[0], list) else (metadatas or [])
        ids_list = ids[0] if ids and isinstance(ids[0], list) else (ids or [])

        if not docs:
            return Response({"error":"No relevant documents found"}, status=status.HTTP_404_NOT_FOUND)

        context_text = "\n\n".join(docs[:3])
        try:
            # order: context, question
            answer = generate_response(context_text, query)
        except Exception:
            logger.exception("LLM generation failed")
            return Response({"error":"Failed to generate answer"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        QueryHistory.objects.create(user=user, query_text=query, top_ids=str(ids_list), answer=answer)

        sources = [{"chunk_text": docs[i], "metadata": metas[i] if i < len(metas) else {}} for i in range(len(docs))]
        return Response({"answer": answer, "sources": sources}, status=status.HTTP_200_OK)
