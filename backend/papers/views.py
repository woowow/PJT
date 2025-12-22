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

    with connection.cursor() as cursor:
        for hit in res["hits"]["hits"]:
            src = hit["_source"]
            paper_id = src.get("id") or hit["_id"]

            # 🔹 저자 목록 (PostgreSQL)
            cursor.execute("""
                SELECT
                    a.author_id,
                    a.author_name
                FROM authorpaper ap
                JOIN author a ON ap.author_id = a.author_id
                WHERE ap.paper_id = %s
                ORDER BY a.author_name
            """, [paper_id])

            authors = [
                {"author_id": r[0], "author_name": r[1]}
                for r in cursor.fetchall()
            ]

            results.append({
                "id": paper_id,
                "title": src.get("title"),
                "authors": authors,                 # ✅ 핵심
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
        # 논문 기본 정보
        cursor.execute("""
            SELECT
                p.paper_id AS id,
                p.title,
                EXTRACT(YEAR FROM p.announcement_date) AS year,
                p.citation,
                i.institution_name AS institution,
                c.category_name AS subject,
                ab.context AS abstract
            FROM paper p
            LEFT JOIN institution i ON p.institution_id = i.institution_id
            LEFT JOIN category c ON p.category_id = c.category_id
            LEFT JOIN abstract ab ON p.paper_id = ab.paper_id
            WHERE p.paper_id = %s
        """, [paper_id])

        paper_row = cursor.fetchone()
        if not paper_row:
            return JsonResponse({"error": "not found"}, status=404)

        paper = {
            "id": paper_row[0],
            "title": paper_row[1],
            "year": int(paper_row[2]) if paper_row[2] else None,
            "citation": paper_row[3],
            "institution": paper_row[4],
            "subject": paper_row[5],
            "abstract": paper_row[6],
        }

        # 저자 목록
        cursor.execute("""
            SELECT
                a.author_id,
                a.author_name
            FROM authorpaper ap
            JOIN author a ON ap.author_id = a.author_id
            WHERE ap.paper_id = %s
            ORDER BY a.author_name
        """, [paper_id])

        paper["authors"] = [
            {"author_id": r[0], "author_name": r[1]}
            for r in cursor.fetchall()
        ]

    return JsonResponse(paper)


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

    with connection.cursor() as cursor:
        for hit in res["hits"]["hits"]:
            src = hit["_source"]
            paper_id = src.get("id")

            # 🔹 저자 목록 (PostgreSQL)
            cursor.execute("""
                SELECT
                    a.author_id,
                    a.author_name
                FROM authorpaper ap
                JOIN author a ON ap.author_id = a.author_id
                WHERE ap.paper_id = %s
                ORDER BY a.author_name
            """, [paper_id])

            authors = [
                {"author_id": r[0], "author_name": r[1]}
                for r in cursor.fetchall()
            ]

            results.append({
                "id": paper_id,
                "title": src.get("title"),
                "authors": authors,                 # ✅ 핵심
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
    
def author_detail(request, author_id):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                a.author_id,
                a.author_name,
                a.citation_total,
                a.main_topic_1,
                a.main_topic_2,
                a.main_topic_3,
                i.institution_name,
                i.country_code
            FROM author a
            LEFT JOIN institution i ON a.institution_id = i.institution_id
            WHERE a.author_id = %s
        """, [author_id])

        row = cursor.fetchone()
        if not row:
            return JsonResponse({"error": "not found"}, status=404)

        author = {
            "author_id": row[0],
            "author_name": row[1],
            "citation_total": row[2],
            "institution": {
                "institution_name": row[6],
                "country_code": row[7],
            },
            "main_topics": [t for t in row[3:6] if t],
        }

        cursor.execute("""
            SELECT
                p.paper_id AS id,
                p.title,
                EXTRACT(YEAR FROM p.announcement_date) AS year,
                p.citation
            FROM paper p
            JOIN authorpaper ap ON p.paper_id = ap.paper_id
            WHERE ap.author_id = %s
            ORDER BY p.announcement_date DESC
        """, [author_id])

        papers = dictfetchall(cursor)

    return JsonResponse({
        "author": author,
        "papers": papers
    })
    
    
@csrf_exempt
def toggle_favorite(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    body = json.loads(request.body)
    guest_id = body.get("guest_id")
    paper_id = body.get("paper_id")

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT favorite_id
            FROM guestfavorite
            WHERE guest_id = %s AND paper_id = %s
        """, [guest_id, paper_id])

        row = cursor.fetchone()

        if row:
            cursor.execute("""
                DELETE FROM guestfavorite
                WHERE favorite_id = %s
            """, [row[0]])
            return JsonResponse({"favorited": False})

        else:
            cursor.execute("""
                INSERT INTO guestfavorite (guest_id, paper_id, status)
                VALUES (%s, %s, 'TODO')
            """, [guest_id, paper_id])
            return JsonResponse({"favorited": True})


def favorite_list(request, guest_id):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                p.paper_id AS id,
                p.title,
                EXTRACT(YEAR FROM p.announcement_date) AS year,
                p.citation,
                gf.status
            FROM guestfavorite gf
            JOIN paper p ON gf.paper_id = p.paper_id
            WHERE gf.guest_id = %s
            ORDER BY p.announcement_date DESC
        """, [guest_id])

        favorites = dictfetchall(cursor)

        # 🔥 authors 수동으로 명확히 만들어준다
        for paper in favorites:
            cursor.execute("""
                SELECT
                    a.author_id,
                    a.author_name
                FROM authorpaper ap
                JOIN author a ON ap.author_id = a.author_id
                WHERE ap.paper_id = %s
                ORDER BY a.author_name
            """, [paper["id"]])

            paper["authors"] = [
                {
                    "author_id": row[0],
                    "author_name": row[1]
                }
                for row in cursor.fetchall()
            ]

    return JsonResponse(favorites, safe=False)

def guest_profile(request, guest_id):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                guest_id,
                guestname,
                interest_1,
                interest_2,
                interest_3
            FROM guest
            WHERE guest_id = %s
        """, [guest_id])

        row = cursor.fetchone()
        if not row:
            return JsonResponse({"error": "not found"}, status=404)

        return JsonResponse({
            "guest_id": row[0],
            "guestname": row[1],
            "interest_1": row[2],
            "interest_2": row[3],
            "interest_3": row[4],
        })

@csrf_exempt
def update_guest(request, guest_id):
    if request.method != "PUT":
        return JsonResponse({"error": "PUT only"}, status=405)

    body = json.loads(request.body)
    guestname = body.get("guestname")
    password = body.get("password")

    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE guest
            SET guestname = %s,
                pwd = %s
            WHERE guest_id = %s
        """, [guestname, password, guest_id])

    return JsonResponse({"message": "updated"})

@csrf_exempt
def update_favorite_status(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    body = json.loads(request.body)
    guest_id = body.get("guest_id")
    paper_id = body.get("paper_id")
    status = body.get("status")

    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE guestfavorite
            SET status = %s
            WHERE guest_id = %s AND paper_id = %s
        """, [status, guest_id, paper_id])

    return JsonResponse({"message": "status updated"})