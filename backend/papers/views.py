from datetime import datetime
from django.db.models import Q, Count
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Paper


from .models import (
    Paper, Category, Guest, GuestFavorite, GuestCategoryCount
)
from .serializers import (
    PaperSerializer, PaperDetailSerializer, GuestFavoriteSerializer
)

# --------------------------------------------------------
# 📌 1. 일반 검색 + 기준 검색 (최신순, 인용순)
# --------------------------------------------------------
@api_view(["GET"])
def search_papers(request):
    keyword = request.GET.get("q", "")
    limit = int(request.GET.get("limit", 10))

    # 기본 필터
    qs = Paper.objects.filter(
        Q(title__icontains=keyword) |
        Q(submit__icontains=keyword)
    )

    # 정렬 옵션
    order = request.GET.get("order", "latest")  
    if order == "latest":
        qs = qs.order_by("-announcement_date")
    elif order == "cited":
        qs = qs.order_by("-citation")

    qs = qs[:limit]

    return Response(PaperSerializer(qs, many=True).data)


# --------------------------------------------------------
# 📌 2. 상세 검색
# --------------------------------------------------------
@api_view(["GET"])
def advanced_search(request):
    qs = Paper.objects.all()

    # 기간 조건
    start = request.GET.get("start")
    end = request.GET.get("end")
    if start:
        qs = qs.filter(announcement_date__gte=start)
    if end:
        qs = qs.filter(announcement_date__lte=end)

    # category 조건
    category_id = request.GET.get("category_id")
    if category_id:
        qs = qs.filter(category_id=category_id)

    # 기관 국가코드
    country = request.GET.get("country")
    if country:
        qs = qs.filter(institution__country_code=country)

    # 오픈액세스
    oa = request.GET.get("open_access")
    if oa in ["true", "True", "1"]:
        qs = qs.filter(open_access=True)

    # 정렬 옵션
    order = request.GET.get("order", "latest")
    if order == "latest":
        qs = qs.order_by("-announcement_date")
    elif order == "cited":
        qs = qs.order_by("-citation")

    return Response(PaperSerializer(qs, many=True).data)


# --------------------------------------------------------
# 📌 3. 논문 상세 API
# --------------------------------------------------------
@api_view(["GET"])
def paper_detail(request, pid):
    try:
        paper = Paper.objects.get(pk=pid)
    except Paper.DoesNotExist:
        return Response({"error": "Paper not found"}, status=404)

    return Response(PaperDetailSerializer(paper).data)


# --------------------------------------------------------
# 📌 4. 주간 인기 논문
# --------------------------------------------------------
@api_view(["GET"])
def weekly_popular_papers(request):
    limit = int(request.GET.get("limit", 10))
    qs = Paper.objects.order_by("-weekly_count")[:limit]
    return Response(PaperSerializer(qs, many=True).data)


# --------------------------------------------------------
# 📌 5. 전체 인기 Category (트렌드)
# --------------------------------------------------------
@api_view(["GET"])
def trending_categories(request):
    qs = (
        GuestCategoryCount.objects
        .values("category_id")
        .annotate(total=Sum("count"))
        .order_by("-total")
    )

    return Response(qs)


# --------------------------------------------------------
# 📌 6. Guest 관심주제 기반 추천
# --------------------------------------------------------
@api_view(["GET"])
def recommend_by_guest(request, guest_id):
    try:
        guest = Guest.objects.get(pk=guest_id)
    except Guest.DoesNotExist:
        return Response({"error": "Guest not found"}, status=404)

    interest_ids = []
    for field in ["interest_1", "interest_2", "interest_3"]:
        cid = getattr(guest, field, None)
        if cid:
            interest_ids.append(cid)

    qs = Paper.objects.filter(category_id__in=interest_ids)

    return Response(PaperSerializer(qs, many=True).data)


# --------------------------------------------------------
# 📌 7. Guest 즐겨찾기 목록
# --------------------------------------------------------
@api_view(["GET"])
def guest_favorites(request, guest_id):
    favs = GuestFavorite.objects.filter(guest_id=guest_id)
    return Response(GuestFavoriteSerializer(favs, many=True).data)


# --------------------------------------------------------
# 📌 8. 즐겨찾기 추가/삭제
# --------------------------------------------------------
@api_view(["POST"])
def toggle_favorite(request):
    guest_id = request.data.get("guest_id")
    paper_id = request.data.get("paper_id")

    obj, created = GuestFavorite.objects.get_or_create(
        guest_id=guest_id,
        paper_id=paper_id
    )

    if not created:
        obj.delete()
        return Response({"status": "removed"})

    return Response({"status": "added"})

## Weekly_count reset

@api_view(["POST"])
def reset_weekly(request):
    Paper.objects.update(weekly_count=0)
    return Response({"status": "ok", "msg": "weekly_count reset"})