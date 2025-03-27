from django.urls import path
from . import views
from .views import QueryAPIView
urlpatterns = [
    path('api/query/', QueryAPIView.as_view(), name='query_api'),
]




