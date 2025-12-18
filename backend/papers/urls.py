from django.urls import path
from .views import paper_list, paper_detail
from .views import register, login

urlpatterns = [
    path("papers/", paper_list),
    path("papers/<int:paper_id>/", paper_detail),
]

urlpatterns += [
    path("auth/register/", register),
    path("auth/login/", login),
]