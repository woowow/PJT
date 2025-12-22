from django.urls import path
from .views import paper_list, paper_detail, register, login, paper_advanced_search, search_options, author_detail

urlpatterns = [
    path("papers/", paper_list),
    path("papers/search/advanced/", paper_advanced_search),
    path("papers/search/options/", search_options),
    path("papers/<int:paper_id>/", paper_detail),
    path("auth/register/", register),
    path("auth/login/", login),
    path("authors/<int:author_id>/", author_detail),
]
