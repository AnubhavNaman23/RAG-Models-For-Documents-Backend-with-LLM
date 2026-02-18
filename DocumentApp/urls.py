from django.contrib import admin
from django.urls import path
from .views import index, DocumentUploadView, SearchView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", index, name="index"),
    path("upload/", DocumentUploadView.as_view(), name="upload"),
    path("search/", SearchView.as_view(), name="search"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)