# papers/views.py
from django.http import JsonResponse
from django.db.models import Q

from .models import Paper
from papers.services.arxiv_api import search_arxiv
from papers.services.kafka_producer import publish_paper_event


# 최신 논문 저장 (Pre-Fetch)
def fetch_and_save_papers(request):
    keyword = request.GET.get("q", "machine learning")

    results = search_arxiv(keyword)
    saved_count = 0

    for p in results:
        obj, created = Paper.objects.get_or_create(
            arxiv_id=p["arxiv_id"],
            defaults={
                "title": p["title"],
                "authors": ", ".join(p["authors"]),
                "abstract": p["summary"],
                "published": p["published"],
                "updated": p["updated"],
                "categories": p["categories"],
                "pdf_url": p["pdf_url"],
            }
        )

        if created:
            saved_count += 1
            publish_paper_event(obj)

    return JsonResponse({
        "status": "ok",
        "fetched": len(results),
        "saved_new": saved_count,
    })

# Lazy Fetch 기반 검색 API
def search_papers(request):
    keyword = request.GET.get("q")

    # 1) DB 검색
    qs = Paper.objects.filter(
        Q(title__icontains=keyword) |
        Q(abstract__icontains=keyword) |
        Q(categories__icontains=keyword)
    )

    results = list(qs.values())

    # Lazy Fetch 조건: DB 결과 적으면 arXiv 호출
    if len(results) < 2:
        arxiv_results = search_arxiv(keyword)

        for p in arxiv_results:
            Paper.objects.get_or_create(
                arxiv_id=p["arxiv_id"],
                defaults={
                    "title": p["title"],
                    "authors": ", ".join(p["authors"]),
                    "abstract": p["summary"],
                    "published": p["published"],
                    "updated": p["updated"],
                    "categories": p["categories"],
                    "pdf_url": p["pdf_url"],
                }
            )

        # DB 다시 조회
        qs = Paper.objects.filter(
            Q(title__icontains=keyword) |
            Q(abstract__icontains=keyword) |
            Q(categories__icontains=keyword)
        )
        results = list(qs.values())

    return JsonResponse({"count": len(results), "results": results})
