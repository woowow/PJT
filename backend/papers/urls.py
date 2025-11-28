from django.urls import path
from .views import (
    search_papers, advanced_search, paper_detail,
    weekly_popular_papers, trending_categories,
    recommend_by_guest, guest_favorites, toggle_favorite, reset_weekly
)

urlpatterns = [
    path("search/", search_papers),
    path("advanced-search/", advanced_search),
    path("detail/<int:pid>/", paper_detail),

    # 인기
    path("popular-weekly/", weekly_popular_papers),
    path("trending-category/", trending_categories),

    # 추천
    path("recommend/<int:guest_id>/", recommend_by_guest),

    # 즐겨찾기
    path("favorites/<int:guest_id>/", guest_favorites),
    path("toggle-favorite/", toggle_favorite),
    
    # weekly_count 초기화
    path("reset-weekly/", reset_weekly),
]
