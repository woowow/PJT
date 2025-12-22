from django.urls import path
from .views import (
    paper_list,
    paper_detail,
    register,
    login,
    paper_advanced_search,
    search_options,
    author_detail,
    toggle_favorite,
    favorite_list,
    guest_profile,
    update_guest,
    update_favorite_status,
    track_paper_action,
    trend_topics,
    trend_papers,
)

urlpatterns = [
    path("papers/", paper_list),
    path("papers/search/advanced/", paper_advanced_search),
    path("papers/search/options/", search_options),
    path("papers/<int:paper_id>/", paper_detail),

    # ✅ 추가: 상세보기/조회 트래킹
    path("papers/<int:paper_id>/track/", track_paper_action),

    # ✅ Trend API
    path("trend/topics/", trend_topics),
    path("trend/papers/", trend_papers),

    path("auth/register/", register),
    path("auth/login/", login),
    path("authors/<int:author_id>/", author_detail),
    path("favorites/toggle/", toggle_favorite),
    path("favorites/<int:guest_id>/", favorite_list),
    path("guests/<int:guest_id>/", guest_profile),
    path("guests/<int:guest_id>/update/", update_guest),
    path("favorites/status/", update_favorite_status),
]
