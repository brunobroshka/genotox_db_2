from django.urls import path
from .views import ProcessAPIView, DownloadAPIView

urlpatterns = [
    path('api/process/', ProcessAPIView.as_view(), name='process_api'),
    path('api/download/', DownloadAPIView.as_view(), name='download_api'),
]




