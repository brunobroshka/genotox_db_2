from django.urls import path
from . import views
from .views import QueryAPIView
urlpatterns = [
    path('query/', QueryAPIView.as_view(), name='query_api'),
]




