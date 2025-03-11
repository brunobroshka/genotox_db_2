from django.urls import path
from . import views

urlpatterns = [
    path('query/', views.query_view, name='query_view'),
    path('', views.query_view, name='root_query'),  # Default route for query view
]




