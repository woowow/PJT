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

    # ✅ 스트리밍 집계(Flink)를 쓰면 DB 직접 집계는 스킵 (중복 방지)
    if not _use_stream_tracking():
        with transaction.atomic():
            with connection.cursor() as cursor:
                ok = _track_interest(cursor, guest_id_int, paper_id)
                if not ok:
                    return JsonResponse({"error": "paper not found"}, status=404)

    # ✅ Kafka 이벤트 발행(실패해도 API는 성공)
    try:
        publish_user_event(guest_id_int, paper_id, "VIEW_DETAIL", meta={"source": "web"})
    except Exception:
        logger.exception(
            "Kafka publish failed (VIEW_DETAIL) guest_id=%s paper_id=%s",
            guest_id_int, paper_id
        )

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

            # ----------------------
            # 이미 즐겨찾기면 삭제
            # ----------------------
            if row:
                cursor.execute("""
                    DELETE FROM guestfavorite
                    WHERE favorite_id = %s
                """, [row[0]])

                action = "FAVORITE_REMOVE"

                # ✅ Kafka 이벤트 발행
                try:
                    publish_user_event(guest_id_int, paper_id_int, action, meta={"source": "web"})
                except Exception:
                    logger.exception(
                        "Kafka publish failed (%s) guest_id=%s paper_id=%s",
                        action, guest_id_int, paper_id_int
                    )

                # (보통 즐겨찾기 해제는 집계 감소 안 함: 지금 설계 유지)
                return JsonResponse({"favorited": False})

            # ----------------------
            # 즐겨찾기 추가
            # ----------------------
            cursor.execute("""
                INSERT INTO guestfavorite (guest_id, paper_id, status)
                VALUES (%s, %s, 'TODO')
            """, [guest_id_int, paper_id_int])

            action = "FAVORITE_ADD"

    # ✅ 스트리밍 집계(Flink)를 쓰면 DB 직접 집계는 스킵 (중복 방지)
    if not _use_stream_tracking():
        try:
            with transaction.atomic():
                with connection.cursor() as tcursor:
                    _track_interest(tcursor, guest_id_int, paper_id_int)
        except Exception as e:
            logger.exception(
                "Tracking failed but favorite kept. guest_id=%s paper_id=%s err=%s",
                guest_id_int, paper_id_int, str(e)
            )

    # ✅ Kafka 이벤트 발행(트래킹 실패 여부와 무관)
    try:
        publish_user_event(guest_id_int, paper_id_int, action, meta={"source": "web"})
    except Exception:
        logger.exception(
            "Kafka publish failed (%s) guest_id=%s paper_id=%s",
            action, guest_id_int, paper_id_int
        )

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
