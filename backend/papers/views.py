from django.http import JsonResponse
from django.db import connection, transaction
from django.views.decorators.csrf import csrf_exempt
import json
from elasticsearch import Elasticsearch
import os
import logging
from psycopg2 import sql as psql

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

    # 필수 컬럼 체크 (없으면 애초에 구조가 다름)
    required = {"guest_id", "category_id"}
    if not required.issubset(names):
        raise RuntimeError(f"guestcategorycount table must have columns {required}, but has {sorted(names)}")

    candidates = ["cnt", "count", "total_cnt", "view_count", "click_count", "read_count", "hit_count", "num"]
    for c in candidates:
        if c in names:
            _GCC_COUNTER_COL = c
            return c

    # fallback: integer/bigint 계열 컬럼 중 (pk/foreign 제외) 하나 선택
    for col_name, data_type in cols:
        if col_name in {"ucc_id", "guest_id", "category_id"}:
            continue
        if data_type in {"integer", "bigint", "smallint"}:
            _GCC_COUNTER_COL = col_name
            return col_name

    # 진짜 없으면: 컬럼 추가가 필요
    raise RuntimeError(
        "guestcategorycount에 증가시킬 카운트 컬럼이 없습니다. "
        "cnt(integer) 같은 컬럼을 추가하거나, 기존 카운트 컬럼명을 코드 후보군에 추가하세요."
    )

def _paper_has_weekly_count(cursor):
    """
    paper.weekly_count 존재 여부 캐시
    """
    global _PAPER_WEEKLY_COL_OK
    if _PAPER_WEEKLY_COL_OK is not None:
        return _PAPER_WEEKLY_COL_OK

    cols = _get_table_columns(cursor, "paper")
    names = {c[0] for c in cols}
    _PAPER_WEEKLY_COL_OK = ("weekly_count" in names)
    return _PAPER_WEEKLY_COL_OK


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
    # weekly_count 컬럼이 없으면 집계만 스킵 (즐겨찾기 기능은 살아야 함)
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
    cnt 컬럼명이 환경마다 다를 수 있어 자동탐지.
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
    """
    category_id = _get_paper_category_id(cursor, paper_id)
    if category_id is None:
        return False

    _increment_weekly_count(cursor, paper_id)
    _upsert_guest_categorycount(cursor, guest_id, category_id)
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
# 📄 논문 상세 (PostgreSQL)
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
# ✅ 관심/조회 트래킹 (필요 시)
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

    # 이 API는 트래킹이 목적이라 실패는 실패로 반환
    with transaction.atomic():
        with connection.cursor() as cursor:
            ok = _track_interest(cursor, guest_id_int, paper_id)
            if not ok:
                return JsonResponse({"error": "paper not found"}, status=404)

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

    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT favorite_id
                FROM guestfavorite
                WHERE guest_id = %s AND paper_id = %s
            """, [guest_id_int, paper_id_int])

            row = cursor.fetchone()

            # 이미 있으면 삭제
            if row:
                cursor.execute("""
                    DELETE FROM guestfavorite
                    WHERE favorite_id = %s
                """, [row[0]])
                return JsonResponse({"favorited": False})

            # 없으면 추가
            cursor.execute("""
                INSERT INTO guestfavorite (guest_id, paper_id, status)
                VALUES (%s, %s, 'TODO')
            """, [guest_id_int, paper_id_int])

    # ✅ 여기부터는 "부가 집계"라서 실패해도 즐겨찾기는 유지되어야 함
    # ✅ savepoint(중첩 atomic)로 분리: 오류 나도 즐겨찾기 INSERT는 이미 커밋 가능
    try:
        with transaction.atomic():
            with connection.cursor() as tcursor:
                _track_interest(tcursor, guest_id_int, paper_id_int)
    except Exception as e:
        logger.exception("Tracking failed but favorite kept. guest_id=%s paper_id=%s err=%s",
                         guest_id_int, paper_id_int, str(e))

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
# (기타 API들 - 기존 그대로)
# ======================
def paper_advanced_search(request):
    keyword = request.GET.get("keyword", "").strip()
    subject = request.GET.get("subject")
    country = request.GET.get("country")
    year_from = request.GET.get("year_from")
    year_to = request.GET.get("year_to")
    sort = request.GET.get("sort", "recent")

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
        filters.append({"term": {"country": country}})

    if year_from or year_to:
        range_q = {}
        if year_from:
            range_q["gte"] = int(year_from)
        if year_to:
            range_q["lte"] = int(year_to)
        filters.append({"range": {"year": range_q}})

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


def trend_topics(request):
    limit = request.GET.get("limit", "10")
    try:
        limit_int = int(limit)
    except ValueError:
        limit_int = 10

    with connection.cursor() as cursor:
        # guestcategorycount 카운트 컬럼은 변동 가능하므로, 여기서도 자동탐지 사용
        try:
            counter_col = _get_gcc_counter_column(cursor)
        except Exception:
            # 카운트 컬럼이 없다면 0으로만 내려줌
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
        # weekly_count 없으면 0 취급 (정렬 기준이 애매하지만 일단 안전하게)
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
