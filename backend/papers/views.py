from django.http import JsonResponse
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
import json
from elasticsearch import Elasticsearch
import os

es = Elasticsearch(os.getenv("ELASTICSEARCH_URL"))

# ======================
# 공통 유틸
# ======================
def dictfetchall(cursor):
    cols = [col[0] for col in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]

# ======================
# 회원가입
# ======================
@csrf_exempt
def register(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    body = json.loads(request.body)
    username = body.get("username")
    password = body.get("password")

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT 1 FROM guest WHERE guestname = %s",
            [username]
        )
        if cursor.fetchone():
            return JsonResponse({"error": "user exists"}, status=409)

        cursor.execute(
            "INSERT INTO guest (guestname, pwd) VALUES (%s, %s)",
            [username, password]
        )

    return JsonResponse({"message": "registered"})

# ======================
# 로그인
# ======================
@csrf_exempt
def login(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    body = json.loads(request.body)
    username = body.get("username")
    password = body.get("password")

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT guest_id FROM guest WHERE guestname=%s AND pwd=%s",
            [username, password]
        )
        row = cursor.fetchone()

    if not row:
        return JsonResponse({"error": "invalid credentials"}, status=401)

    return JsonResponse({"guest_id": row[0]})

# ======================
# 🔍 논문 검색 (ES ONLY)
# ======================
def paper_list(request):
    keyword = request.GET.get("keyword", "").strip()

    query = {
        "size": 100,
        "query": {
            "multi_match": {
                "query": keyword,
                "fields": ["title", "author"]
            } if keyword else {"match_all": {}}
        }
    }

    res = es.search(index="papers", body=query)

    results = []
    for hit in res["hits"]["hits"]:
        src = hit["_source"]
        results.append({
            "id": src.get("id") or hit["_id"],
            "title": src.get("title"),
            "author": src.get("author"),
            "year": src.get("year"),
            "citation": src.get("citation", 0),
            "institution": src.get("institution"),
            "subject": src.get("subject"),
            "country": src.get("country"),
        })

    return JsonResponse(results, safe=False)

# ======================
# 📄 논문 상세 (PostgreSQL)
# ======================
def paper_detail(request, paper_id):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                p.paper_id AS id,
                p.title,
                STRING_AGG(a.author_name, ', ') AS author,
                EXTRACT(YEAR FROM p.announcement_date) AS year,
                p.citation,
                i.institution_name AS institution,
                c.category_name AS subject,
                ab.context AS abstract,
                p.open_access,
                p.locations
            FROM paper p
            LEFT JOIN authorpaper ap ON p.paper_id = ap.paper_id
            LEFT JOIN author a ON ap.author_id = a.author_id
            LEFT JOIN institution i ON p.institution_id = i.institution_id
            LEFT JOIN category c ON p.category_id = c.category_id
            LEFT JOIN abstract ab ON p.paper_id = ab.paper_id
            WHERE p.paper_id = %s
            GROUP BY
                p.paper_id, p.title, p.announcement_date,
                p.citation, i.institution_name,
                c.category_name, ab.context,
                p.open_access, p.locations
        """, [paper_id])

        rows = dictfetchall(cursor)

    if not rows:
        return JsonResponse({"error": "not found"}, status=404)

    return JsonResponse(rows[0])

def paper_advanced_search(request):
    keyword = request.GET.get("keyword", "").strip()
    subject = request.GET.get("subject")
    country = request.GET.get("country")
    year_from = request.GET.get("year_from")
    year_to = request.GET.get("year_to")
    sort = request.GET.get("sort", "recent")

    must = []
    filters = []

    # 🔍 키워드
    if keyword:
        must.append({
            "multi_match": {
                "query": keyword,
                "fields": ["title^2", "author", "subject"]
            }
        })

    # 📌 주제
    if subject:
        filters.append({
            "term": {
                "subject.keyword": subject
            }
        })

    # 🌍 국가
    if country:
        filters.append({
            "term": {
                "country": country
            }
        })

    # 📅 연도
    if year_from or year_to:
        range_q = {}
        if year_from:
            range_q["gte"] = int(year_from)
        if year_to:
            range_q["lte"] = int(year_to)

        filters.append({
            "range": {
                "year": range_q
            }
        })

    # 🔃 정렬
    sort_query = (
        [{"citation": "desc"}]
        if sort == "citation"
        else [{"year": "desc"}]
    )

    query = {
        "size": 100,
        "query": {
            "bool": {
                "must": must if must else [{"match_all": {}}],
                "filter": filters
            }
        },
        "sort": sort_query
    }

    res = es.search(index="papers", body=query)

    results = []
    for hit in res["hits"]["hits"]:
        src = hit["_source"]
        results.append({
            "id": src["id"],
            "title": src["title"],
            "author": src.get("author"),
            "year": src.get("year"),
            "citation": src.get("citation", 0),
            "institution": src.get("institution"),
            "subject": src.get("subject"),
            "country": src.get("country"),
        })

    return JsonResponse(results, safe=False)

def search_options(request):
    with connection.cursor() as cursor:
        # 주제 목록
        cursor.execute("""
            SELECT DISTINCT category_name
            FROM category
            ORDER BY category_name
        """)
        subjects = [row[0] for row in cursor.fetchall()]

        # 국가 목록
        cursor.execute("""
            SELECT DISTINCT country_code
            FROM institution
            WHERE country_code IS NOT NULL
            ORDER BY country_code
        """)
        countries = [row[0] for row in cursor.fetchall()]

    return JsonResponse({
        "subjects": subjects,
        "countries": countries,
    })