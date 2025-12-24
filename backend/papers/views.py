from django.http import JsonResponse
from django.db import connection, transaction
from django.views.decorators.csrf import csrf_exempt
import json
from elasticsearch import Elasticsearch
import os
import logging
from psycopg2 import sql as psql
from .services.kafka_producer import publish_user_event
from django.conf import settings

# ✅ Chatbot
import re
from openai import OpenAI


def _use_stream_tracking() -> bool:
    """
    요청 시점에 settings를 읽어서 결정(캐시/재시작/빌드 꼬임 디버깅 쉬움)
    """
    return bool(getattr(settings, "USE_STREAM_TRACKING", False))


logger = logging.getLogger(__name__)

es = Elasticsearch(os.getenv("ELASTICSEARCH_URL"))

# ======================
# 공통 유틸
# ======================
def dictfetchall(cursor):
    cols = [col[0] for col in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]

def _safe_int(value):
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

# ---- schema introspection cache ----
_GCC_COUNTER_COL = None
_PAPER_WEEKLY_COL_OK = None

def _get_table_columns(cursor, table_name: str):
    cursor.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = %s
    """, [table_name])
    return cursor.fetchall()  # [(name, type), ...]

def _get_gcc_counter_column(cursor):
    """
    guestcategorycount 테이블에서 "카운트" 역할의 컬럼을 자동 탐지.
    우선순위 후보: cnt, count, total_cnt, view_count, click_count, read_count ...
    없으면: (guest_id, category_id, ucc_id를 제외한) integer 컬럼 중 첫 번째 선택.
    """
    global _GCC_COUNTER_COL
    if _GCC_COUNTER_COL:
        return _GCC_COUNTER_COL

    cols = _get_table_columns(cursor, "guestcategorycount")
    names = {c[0] for c in cols}

    required = {"guest_id", "category_id"}
    if not required.issubset(names):
        raise RuntimeError(f"guestcategorycount table must have columns {required}, but has {sorted(names)}")

    candidates = ["cnt", "count", "total_cnt", "view_count", "click_count", "read_count", "hit_count", "num"]
    for c in candidates:
        if c in names:
            _GCC_COUNTER_COL = c
            return c

    for col_name, data_type in cols:
        if col_name in {"ucc_id", "guest_id", "category_id"}:
            continue
        if data_type in {"integer", "bigint", "smallint"}:
            _GCC_COUNTER_COL = col_name
            return col_name

    raise RuntimeError(
        "guestcategorycount에 증가시킬 카운트 컬럼이 없습니다. "
        "cnt(integer) 같은 컬럼을 추가하거나, 기존 카운트 컬럼명을 코드 후보군에 추가하세요."
    )

def _paper_has_weekly_count(cursor):
    global _PAPER_WEEKLY_COL_OK
    if _PAPER_WEEKLY_COL_OK is not None:
        return _PAPER_WEEKLY_COL_OK

    cols = _get_table_columns(cursor, "paper")
    names = {c[0] for c in cols}
    _PAPER_WEEKLY_COL_OK = ("weekly_count" in names)
    return _PAPER_WEEKLY_COL_OK


# ======================
# ✅ 관심 주제 TOP3 자동 갱신
# ======================
def _get_top_categories_for_guest(cursor, guest_id: int, topn: int = 3):
    """
    guestcategorycount에서 guest_id 기준으로 카운트가 높은 카테고리 TOP N의 category_name 목록 반환
    """
    counter_col = _get_gcc_counter_column(cursor)

    q = psql.SQL("""
        SELECT c.category_name
        FROM guestcategorycount gcc
        JOIN category c ON gcc.category_id = c.category_id
        WHERE gcc.guest_id = %s
        ORDER BY gcc.{col} DESC, c.category_name ASC
        LIMIT %s
    """).format(col=psql.Identifier(counter_col))

    cursor.execute(q, [guest_id, topn])
    return [r[0] for r in cursor.fetchall()]

def _refresh_guest_interests(cursor, guest_id: int):
    """
    guest.interest_1~3을 guestcategorycount TOP3로 업데이트
    """
    try:
        top = _get_top_categories_for_guest(cursor, guest_id, 3)
    except Exception:
        # guestcategorycount 구조가 이상한 경우 등: 업데이트 스킵
        return

    interests = (top + [None, None, None])[:3]

    cursor.execute("""
        UPDATE guest
        SET interest_1 = %s,
            interest_2 = %s,
            interest_3 = %s
        WHERE guest_id = %s
    """, [interests[0], interests[1], interests[2], guest_id])


# ======================
# 트래킹 로직
# ======================
def _get_paper_category_id(cursor, paper_id):
    cursor.execute("""
        SELECT category_id
        FROM paper
        WHERE paper_id = %s
    """, [paper_id])
    row = cursor.fetchone()
    return row[0] if row else None

def _increment_weekly_count(cursor, paper_id):
    if not _paper_has_weekly_count(cursor):
        return

    cursor.execute("""
        UPDATE paper
        SET weekly_count = weekly_count + 1
        WHERE paper_id = %s
    """, [paper_id])

def _upsert_guest_categorycount(cursor, guest_id, category_id):
    """
    guestcategorycount(guest_id, category_id)의 카운트를 +1.
    UNIQUE(guest_id, category_id)가 없어도 동작하도록 CTE upsert 사용.
    """
    counter_col = _get_gcc_counter_column(cursor)

    q = psql.SQL("""
        WITH updated AS (
          UPDATE guestcategorycount
          SET {col} = {col} + 1
          WHERE guest_id = %s AND category_id = %s
          RETURNING ucc_id
        )
        INSERT INTO guestcategorycount (guest_id, category_id, {col})
        SELECT %s, %s, 1
        WHERE NOT EXISTS (SELECT 1 FROM updated);
    """).format(col=psql.Identifier(counter_col))

    cursor.execute(q, [guest_id, category_id, guest_id, category_id])

def _track_interest(cursor, guest_id, paper_id):
    """
    1) paper.weekly_count += 1  (없으면 skip)
    2) guestcategorycount(guest_id, paper.category_id).카운트 += 1 (없으면 생성)
    3) ✅ guest.interest_1~3 TOP3 갱신
    """
    category_id = _get_paper_category_id(cursor, paper_id)
    if category_id is None:
        return False

    _increment_weekly_count(cursor, paper_id)
    _upsert_guest_categorycount(cursor, guest_id, category_id)

    # ✅ 여기서 TOP3 갱신
    _refresh_guest_interests(cursor, guest_id)

    return True


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

            raw_id = src.get("id") or hit.get("_id")
            paper_id = _safe_int(raw_id)
            if paper_id is None:
                continue

            cursor.execute("""
                SELECT a.author_id, a.author_name
                FROM authorpaper ap
                JOIN author a ON ap.author_id = a.author_id
                WHERE ap.paper_id = %s
                ORDER BY a.author_name
            """, [paper_id])

            authors = [{"author_id": r[0], "author_name": r[1]} for r in cursor.fetchall()]

            results.append({
                "id": paper_id,
                "title": src.get("title"),
                "authors": authors,
                "year": src.get("year"),
                "citation": src.get("citation", 0),
                "institution": src.get("institution"),
                "subject": src.get("subject"),
                "country": src.get("country"),
            })

    return JsonResponse(results, safe=False)


# ======================
# 📄 논문 상세 (PostgreSQL)  ✅ 필드 확장
# ======================
def paper_detail(request, paper_id):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                p.paper_id AS id,
                p.title,
                EXTRACT(YEAR FROM p.announcement_date) AS year,
                p.citation,
                i.institution_name AS institution,
                c.category_name AS subject,
                ab.context AS abstract,

                -- ✅ 추가
                p.locations,
                p.open_access,
                p.announcement_date
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

            # ✅ 추가
            "locations": paper_row[7],
            "open_access": paper_row[8],
            "announcement_date": paper_row[9].isoformat() if paper_row[9] else None,
        }

        cursor.execute("""
            SELECT a.author_id, a.author_name
            FROM authorpaper ap
            JOIN author a ON ap.author_id = a.author_id
            WHERE ap.paper_id = %s
            ORDER BY a.author_name
        """, [paper_id])

        paper["authors"] = [{"author_id": r[0], "author_name": r[1]} for r in cursor.fetchall()]

    return JsonResponse(paper)


# ======================
# ✅ 관심/조회 트래킹
# ======================
@csrf_exempt
def track_paper_action(request, paper_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        body = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        body = {}

    guest_id = body.get("guest_id")
    if not guest_id:
        return JsonResponse({"error": "guest_id required"}, status=400)

    try:
        guest_id_int = int(guest_id)
    except (TypeError, ValueError):
        return JsonResponse({"error": "guest_id must be integer"}, status=400)

    with connection.cursor() as cursor:
        cursor.execute("SELECT 1 FROM paper WHERE paper_id=%s", [paper_id])
        if not cursor.fetchone():
            return JsonResponse({"error": "paper not found"}, status=404)

    try:
        publish_user_event(guest_id_int, paper_id, "VIEW_DETAIL", meta={"source": "web"})
    except Exception:
        logger.exception("Kafka publish failed (VIEW_DETAIL) guest_id=%s paper_id=%s", guest_id_int, paper_id)

    return JsonResponse({"ok": True})


# ======================
# 즐겨찾기 토글
# ======================
@csrf_exempt
def toggle_favorite(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    body = json.loads(request.body)
    guest_id = body.get("guest_id")
    paper_id = body.get("paper_id")

    if guest_id is None or paper_id is None:
        return JsonResponse({"error": "guest_id and paper_id required"}, status=400)

    try:
        guest_id_int = int(guest_id)
        paper_id_int = int(paper_id)
    except (TypeError, ValueError):
        return JsonResponse({"error": "guest_id and paper_id must be integer"}, status=400)

    action = None

    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT favorite_id
                FROM guestfavorite
                WHERE guest_id = %s AND paper_id = %s
            """, [guest_id_int, paper_id_int])

            row = cursor.fetchone()

            if row:
                cursor.execute("""
                    DELETE FROM guestfavorite
                    WHERE favorite_id = %s
                """, [row[0]])
                action = "FAVORITE_REMOVE"
            else:
                cursor.execute("""
                    INSERT INTO guestfavorite (guest_id, paper_id, status)
                    VALUES (%s, %s, 'TODO')
                """, [guest_id_int, paper_id_int])
                action = "FAVORITE_ADD"

    try:
        publish_user_event(guest_id_int, paper_id_int, action, meta={"source": "web"})
    except Exception:
        logger.exception("Kafka publish failed (%s) guest_id=%s paper_id=%s", action, guest_id_int, paper_id_int)

    return JsonResponse({"favorited": (action == "FAVORITE_ADD")})


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

        for paper in favorites:
            cursor.execute("""
                SELECT a.author_id, a.author_name
                FROM authorpaper ap
                JOIN author a ON ap.author_id = a.author_id
                WHERE ap.paper_id = %s
                ORDER BY a.author_name
            """, [paper["id"]])

            paper["authors"] = [{"author_id": row[0], "author_name": row[1]} for row in cursor.fetchall()]

    return JsonResponse(favorites, safe=False)


# ======================
# 🔎 상세 검색
# ======================
def paper_advanced_search(request):
    def get_any(*keys, default=""):
        for k in keys:
            v = request.GET.get(k)
            if v is not None and str(v).strip() != "":
                return str(v).strip()
        return default

    keyword = get_any("keyword", "q")
    subject = get_any("subject", "category", "topic", "category_name")
    country = get_any("country", "country_code", "countryCode")
    year_from = get_any("year_from", "yearFrom", "from")
    year_to = get_any("year_to", "yearTo", "to")
    sort = get_any("sort", "order", default="recent") or "recent"

    must = []
    filters = []

    if keyword:
        must.append({
            "multi_match": {
                "query": keyword,
                "fields": ["title^2", "author", "subject"]
            }
        })

    if subject:
        filters.append({"term": {"subject.keyword": subject}})

    if country:
        filters.append({"term": {"country.keyword": country}})

    if year_from or year_to:
        range_q = {}
        try:
            if year_from:
                range_q["gte"] = int(year_from)
            if year_to:
                range_q["lte"] = int(year_to)
            filters.append({"range": {"year": range_q}})
        except ValueError:
            pass

    sort_query = ([{"citation": "desc"}] if sort == "citation" else [{"year": "desc"}])

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
            raw_id = src.get("id") or hit.get("_id")
            paper_id = _safe_int(raw_id)
            if paper_id is None:
                continue

            cursor.execute("""
                SELECT a.author_id, a.author_name
                FROM authorpaper ap
                JOIN author a ON ap.author_id = a.author_id
                WHERE ap.paper_id = %s
                ORDER BY a.author_name
            """, [paper_id])

            authors = [{"author_id": r[0], "author_name": r[1]} for r in cursor.fetchall()]

            results.append({
                "id": paper_id,
                "title": src.get("title"),
                "authors": authors,
                "year": src.get("year"),
                "citation": src.get("citation", 0),
                "institution": src.get("institution"),
                "subject": src.get("subject"),
                "country": src.get("country"),
            })

    return JsonResponse(results, safe=False)


def search_options(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT category_name
            FROM category
            ORDER BY category_name
        """)
        subjects = [row[0] for row in cursor.fetchall()]

        cursor.execute("""
            SELECT DISTINCT country_code
            FROM institution
            WHERE country_code IS NOT NULL
            ORDER BY country_code
        """)
        countries = [row[0] for row in cursor.fetchall()]

    return JsonResponse({"subjects": subjects, "countries": countries})


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

    return JsonResponse({"author": author, "papers": papers})


def guest_profile(request, guest_id):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT guest_id, guestname, interest_1, interest_2, interest_3
            FROM guest
            WHERE guest_id = %s
        """, [guest_id])

        row = cursor.fetchone()
        if not row:
            return JsonResponse({"error": "not found"}, status=404)

        interest_1, interest_2, interest_3 = row[2], row[3], row[4]

        try:
            top = _get_top_categories_for_guest(cursor, int(guest_id), 3)
            if top:
                filled = (top + [None, None, None])[:3]
                interest_1, interest_2, interest_3 = filled[0], filled[1], filled[2]
        except Exception:
            pass

        return JsonResponse({
            "guest_id": row[0],
            "guestname": row[1],
            "interest_1": interest_1,
            "interest_2": interest_2,
            "interest_3": interest_3,
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


def trend_topics(request):
    limit = request.GET.get("limit", "10")
    try:
        limit_int = int(limit)
    except ValueError:
        limit_int = 10

    with connection.cursor() as cursor:
        try:
            counter_col = _get_gcc_counter_column(cursor)
        except Exception:
            counter_col = None

        if counter_col:
            q = psql.SQL("""
                SELECT
                    c.category_id,
                    c.category_name,
                    COALESCE(SUM(gcc.{col}), 0) AS total_cnt
                FROM guestcategorycount gcc
                JOIN category c ON gcc.category_id = c.category_id
                GROUP BY c.category_id, c.category_name
                ORDER BY total_cnt DESC, c.category_name ASC
                LIMIT %s
            """).format(col=psql.Identifier(counter_col))
            cursor.execute(q, [limit_int])
            rows = dictfetchall(cursor)
        else:
            cursor.execute("""
                SELECT category_id, category_name, 0 AS total_cnt
                FROM category
                ORDER BY category_name
                LIMIT %s
            """, [limit_int])
            rows = dictfetchall(cursor)

    return JsonResponse(rows, safe=False)


def trend_papers(request):
    limit = request.GET.get("limit", "10")
    try:
        limit_int = int(limit)
    except ValueError:
        limit_int = 10

    with connection.cursor() as cursor:
        if _paper_has_weekly_count(cursor):
            cursor.execute("""
                SELECT
                    p.paper_id AS id,
                    p.title,
                    EXTRACT(YEAR FROM p.announcement_date) AS year,
                    p.citation,
                    i.institution_name AS institution,
                    c.category_name AS subject,
                    p.weekly_count
                FROM paper p
                LEFT JOIN institution i ON p.institution_id = i.institution_id
                LEFT JOIN category c ON p.category_id = c.category_id
                ORDER BY p.weekly_count DESC, p.paper_id DESC
                LIMIT %s
            """, [limit_int])
        else:
            cursor.execute("""
                SELECT
                    p.paper_id AS id,
                    p.title,
                    EXTRACT(YEAR FROM p.announcement_date) AS year,
                    p.citation,
                    i.institution_name AS institution,
                    c.category_name AS subject,
                    0 AS weekly_count
                FROM paper p
                LEFT JOIN institution i ON p.institution_id = i.institution_id
                LEFT JOIN category c ON p.category_id = c.category_id
                ORDER BY p.paper_id DESC
                LIMIT %s
            """, [limit_int])

        papers = dictfetchall(cursor)

        for p in papers:
            cursor.execute("""
                SELECT a.author_id, a.author_name
                FROM authorpaper ap
                JOIN author a ON ap.author_id = a.author_id
                WHERE ap.paper_id = %s
                ORDER BY a.author_name
            """, [p["id"]])

            p["authors"] = [{"author_id": r[0], "author_name": r[1]} for r in cursor.fetchall()]

    return JsonResponse(papers, safe=False)


def recommendation_list(request):
    guest_id = request.GET.get('guest_id')
    if not guest_id:
        return JsonResponse({"error": "guest_id required"}, status=400)

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT gcc.category_id, c.category_name 
                FROM guestcategorycount gcc
                JOIN category c ON gcc.category_id = c.category_id
                WHERE gcc.guest_id = %s 
                ORDER BY gcc.count DESC LIMIT 3
            """, [guest_id])
            top_categories = cursor.fetchall()
            
            if not top_categories:
                return JsonResponse({"results": []})

            all_recommendations = []

            for cat_id, cat_name in top_categories:
                cursor.execute("""
                    SELECT p.paper_id, p.title, p.citation, p.announcement_date, 
                           MAX(a.author_name) as author_name, 'FUNDAMENTAL' as type
                    FROM paper p
                    LEFT JOIN authorpaper ap ON p.paper_id = ap.paper_id
                    LEFT JOIN author a ON ap.author_id = a.author_id
                    WHERE p.category_id = %s 
                    GROUP BY p.paper_id, p.title, p.citation, p.announcement_date
                    ORDER BY p.citation DESC LIMIT 5
                """, [cat_id])
                fundamental_papers = dictfetchall(cursor)

                fundamental_ids = [p['paper_id'] for p in fundamental_papers]
                
                cursor.execute("""
                    SELECT p.paper_id, p.title, p.citation, p.announcement_date, 
                           MAX(a.author_name) as author_name, 'TREND' as type
                    FROM paper p
                    LEFT JOIN authorpaper ap ON p.paper_id = ap.paper_id
                    LEFT JOIN author a ON ap.author_id = a.author_id
                    WHERE p.category_id = %s 
                      AND p.citation >= 1
                      AND p.paper_id NOT IN %s
                    GROUP BY p.paper_id, p.title, p.citation, p.announcement_date
                    ORDER BY p.announcement_date DESC LIMIT 5
                """, [cat_id, tuple(fundamental_ids) if fundamental_ids else (0,)])
                trend_papers = dictfetchall(cursor)
                
                all_recommendations.append({
                    "category_name": cat_name,
                    "fundamental_papers": fundamental_papers,
                    "trend_papers": trend_papers
                })

            return JsonResponse({"results": all_recommendations})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ============================================================
# ✅ Chatbot API (NEW)
# ============================================================

def _looks_like_trend_question(text: str) -> bool:
    t = (text or "").lower()
    keywords = ["트렌드", "weekly", "hot", "인기", "top", "주간", "요즘"]
    return any(k in t for k in keywords)

def _extract_paper_id_hint(text: str):
    if not text:
        return None
    if ("논문" in text) or ("paper" in text.lower()) or ("#" in text):
        m = re.search(r"(?:논문|paper|#)\s*([0-9]{1,7})", text, re.IGNORECASE)
        if m:
            return _safe_int(m.group(1))
    return None

def _fetch_weekly_top(cursor, limit=10):
    if not _paper_has_weekly_count(cursor):
        return []
    cursor.execute("""
        SELECT
            p.paper_id AS id,
            p.title,
            EXTRACT(YEAR FROM p.announcement_date) AS year,
            p.citation,
            c.category_name AS subject,
            p.weekly_count
        FROM paper p
        LEFT JOIN category c ON p.category_id = c.category_id
        ORDER BY p.weekly_count DESC, p.paper_id DESC
        LIMIT %s
    """, [limit])
    return dictfetchall(cursor)

def _fetch_guest_favorites(cursor, guest_id: int, limit=5):
    cursor.execute("""
        SELECT
            p.paper_id AS id,
            p.title,
            EXTRACT(YEAR FROM p.announcement_date) AS year,
            p.citation
        FROM guestfavorite gf
        JOIN paper p ON gf.paper_id = p.paper_id
        WHERE gf.guest_id = %s
        ORDER BY p.announcement_date DESC
        LIMIT %s
    """, [guest_id, limit])
    return dictfetchall(cursor)

def _fetch_guest_top_topics(cursor, guest_id: int, limit=3):
    try:
        counter_col = _get_gcc_counter_column(cursor)
    except Exception:
        counter_col = None
    if not counter_col:
        return []
    q = psql.SQL("""
        SELECT
            c.category_name,
            gcc.{col} AS cnt
        FROM guestcategorycount gcc
        JOIN category c ON gcc.category_id = c.category_id
        WHERE gcc.guest_id = %s
        ORDER BY gcc.{col} DESC, c.category_name ASC
        LIMIT %s
    """).format(col=psql.Identifier(counter_col))
    cursor.execute(q, [guest_id, limit])
    rows = cursor.fetchall()
    return [{"category_name": r[0], "cnt": r[1]} for r in rows]

def _fetch_paper_brief(cursor, paper_id: int):
    cursor.execute("""
        SELECT
            p.paper_id AS id,
            p.title,
            EXTRACT(YEAR FROM p.announcement_date) AS year,
            p.citation,
            i.institution_name AS institution,
            c.category_name AS subject
        FROM paper p
        LEFT JOIN institution i ON p.institution_id = i.institution_id
        LEFT JOIN category c ON p.category_id = c.category_id
        WHERE p.paper_id = %s
    """, [paper_id])
    row = cursor.fetchone()
    if not row:
        return None
    return {
        "id": row[0],
        "title": row[1],
        "year": int(row[2]) if row[2] else None,
        "citation": row[3],
        "institution": row[4],
        "subject": row[5],
    }

def _extract_response_text(resp) -> str:
    try:
        out_text = getattr(resp, "output_text", None)
        if out_text:
            return out_text
    except Exception:
        pass

    try:
        texts = []
        for item in getattr(resp, "output", []) or []:
            if getattr(item, "type", None) == "message":
                for c in getattr(item, "content", []) or []:
                    t = getattr(c, "text", None)
                    if t:
                        texts.append(t)
        if texts:
            return "\n".join(texts).strip()
    except Exception:
        pass

    return ""

@csrf_exempt
def chatbot(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        body = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        body = {}

    message = (body.get("message") or "").strip()
    guest_id = body.get("guest_id")
    history = body.get("history") or []

    if not message:
        return JsonResponse({"error": "message required"}, status=400)

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    base_url = os.getenv("OPENAI_BASE_URL", "").strip() or None  # ✅ 핵심 (GMS)
    model = os.getenv("OPENAI_MODEL", "gpt-4.1").strip()

    try:
        temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))
    except ValueError:
        temperature = 0.3
    try:
        max_out = int(os.getenv("OPENAI_MAX_OUTPUT_TOKENS", "700"))
    except ValueError:
        max_out = 700

    if not api_key or "PUT_YOUR_GMS_KEY_HERE" in api_key:
        return JsonResponse({"error": "OPENAI_API_KEY(GMS_KEY)가 backend/.env에 설정되어야 합니다."}, status=500)

    ctx_lines = []
    meta_used = []

    paper_id_hint = _extract_paper_id_hint(message)

    with connection.cursor() as cursor:
        if paper_id_hint is not None:
            p = _fetch_paper_brief(cursor, paper_id_hint)
            if p:
                ctx_lines.append("[선택 논문 요약]")
                ctx_lines.append(
                    f"- id={p['id']} | {p['title']} ({p.get('year')}) | citation={p.get('citation')} | subject={p.get('subject')} | inst={p.get('institution')}"
                )
                meta_used.append("paper_brief")
            else:
                ctx_lines.append("[선택 논문 요약]")
                ctx_lines.append(f"- id={paper_id_hint} 는 DB에서 찾지 못했습니다.")
                meta_used.append("paper_brief_missing")

        if _looks_like_trend_question(message):
            top = _fetch_weekly_top(cursor, limit=10)
            if top:
                ctx_lines.append("[주간 트렌드(weekly_count) TOP 10]")
                for r in top:
                    ctx_lines.append(
                        f"- id={r['id']} | weekly={r.get('weekly_count')} | {r.get('title')} ({r.get('year')}) | citation={r.get('citation')} | subject={r.get('subject')}"
                    )
                meta_used.append("weekly_top")

        guest_id_int = None
        if guest_id is not None:
            try:
                guest_id_int = int(guest_id)
            except (TypeError, ValueError):
                guest_id_int = None

        if guest_id_int is not None:
            top_topics = _fetch_guest_top_topics(cursor, guest_id_int, limit=3)
            if top_topics:
                ctx_lines.append("[사용자 관심 주제 TOP 3(누적)]")
                for t in top_topics:
                    ctx_lines.append(f"- {t['category_name']} (cnt={t['cnt']})")
                meta_used.append("guest_top_topics")

            fav = _fetch_guest_favorites(cursor, guest_id_int, limit=5)
            if fav:
                ctx_lines.append("[사용자 즐겨찾기 최근 5개]")
                for r in fav:
                    ctx_lines.append(f"- id={r['id']} | {r.get('title')} ({r.get('year')}) | citation={r.get('citation')}")
                meta_used.append("guest_favorites")

    context = "\n".join(ctx_lines).strip()

    instructions = (
        "너는 'Archivinator' 논문 검색/추천 웹서비스의 챗봇이다.\n"
        "- 답변은 한국어로, 짧고 명확하게.\n"
        "- 아래 [Context]에 없는 논문 세부정보는 지어내지 말 것.\n"
        "- 사용자가 '트렌드/인기/weekly'를 물으면 weekly_count 기준으로 정리.\n"
        "- 사용자가 '추천'을 물으면 사용자 관심주제/즐겨찾기(있다면)를 근거로 제안.\n"
        "- 답변에 논문을 제시할 때는 가능하면 paper_id를 함께 적어라.\n"
        "- 불확실하면 불확실하다고 말하고, 어떤 정보를 더 보면 좋은지 안내.\n"
    )

    llm_input = []
    if history and isinstance(history, list):
        trimmed = history[-10:]
        lines = []
        for h in trimmed:
            role = (h.get("role") or "").strip()
            content = (h.get("content") or "").strip()
            if role in ("user", "assistant") and content:
                lines.append(f"{role.upper()}: {content}")
        if lines:
            llm_input.append("[ChatHistory]\n" + "\n".join(lines))

    if context:
        llm_input.append("[Context]\n" + context)

    llm_input.append("[User]\n" + message)
    final_input = "\n\n".join(llm_input).strip()

    try:
        client = OpenAI(api_key=api_key, base_url=base_url)

        resp = client.responses.create(
            model=model,
            instructions=instructions,
            input=final_input,
            temperature=temperature,
            max_output_tokens=max_out,
        )
        reply = _extract_response_text(resp) or ""
        if not reply.strip():
            reply = "답변 생성에 실패했습니다. (빈 응답) 다시 시도해 주세요."
        return JsonResponse({"reply": reply, "meta": {"model": model, "used_context": meta_used, "base_url": base_url}})
    except Exception as e:
        logger.exception("Chatbot error")
        return JsonResponse({"error": str(e)}, status=500)
