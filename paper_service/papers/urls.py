from django.urls import path
from .views import fetch_and_save_papers, search_papers

urlpatterns = [
    path("fetch/", fetch_and_save_papers),
    path("search/", search_papers),
]
