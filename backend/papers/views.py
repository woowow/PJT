from django.http import JsonResponse
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
import json

# 회원가입
@csrf_exempt
def register(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    body = json.loads(request.body)
    username = body.get("username")
    password = body.get("password")

    if not username or not password:
        return JsonResponse({"error": "missing fields"}, status=400)

    with connection.cursor() as cursor:
        # 중복 체크
        cursor.execute(
            "SELECT 1 FROM guest WHERE guestname = %s",
            [username]
        )
        if cursor.fetchone():
            return JsonResponse({"error": "user exists"}, status=409)

        # 저장
        cursor.execute("""
            INSERT INTO guest (guestname, pwd)
            VALUES (%s, %s)
        """, [username, password])

    return JsonResponse({"message": "registered"})

# 로그인
@csrf_exempt
def login(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    body = json.loads(request.body)
    username = body.get("username")
    password = body.get("password")

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT guest_id FROM guest
            WHERE guestname = %s AND pwd = %s
        """, [username, password])

        row = cursor.fetchone()
        if not row:
            return JsonResponse({"error": "invalid credentials"}, status=401)

    return JsonResponse({
        "message": "login success",
        "guest_id": row[0]
    })

def dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


# 🔹 논문 리스트
def paper_list(request):
    keyword = request.GET.get("keyword", "")
    subject = request.GET.get("subject", "")
    country = request.GET.get("country", "")

    conditions = []
    params = []

    if keyword:
        conditions.append("p.title ILIKE %s")
        params.append(f"%{keyword}%")

    if subject:
        conditions.append("""
            (
              p.title ILIKE %s OR
              a.author_name ILIKE %s OR
              c.category_name ILIKE %s
            )
        """)
        params.extend([f"%{subject}%"] * 3)

    if country:
        conditions.append("i.country_code = %s")
        params.append(country)

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    with connection.cursor() as cursor:
        cursor.execute(f"""
            SELECT DISTINCT
                p.paper_id AS id,
                p.title,
                a.author_name AS author,
                EXTRACT(YEAR FROM p.announcement_date) AS year,
                p.citation,
                i.institution_name AS institution
            FROM paper p
            LEFT JOIN authorpaper ap ON p.paper_id = ap.paper_id
            LEFT JOIN author a ON ap.author_id = a.author_id
            LEFT JOIN institution i ON p.institution_id = i.institution_id
            LEFT JOIN category c ON p.category_id = c.category_id
            {where_clause}
            ORDER BY p.citation DESC
            LIMIT 100
        """, params)

        data = dictfetchall(cursor)

    return JsonResponse(data, safe=False)


# 🔹 논문 상세
def paper_detail(request, paper_id):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                p.paper_id AS id,
                p.title,
                a.author_name AS author,
                EXTRACT(YEAR FROM p.announcement_date) AS year,
                p.citation,
                i.institution_name AS institution,
                ab.context AS abstract
            FROM paper p
            LEFT JOIN authorpaper ap ON p.paper_id = ap.paper_id
            LEFT JOIN author a ON ap.author_id = a.author_id
            LEFT JOIN institution i ON p.institution_id = i.institution_id
            LEFT JOIN abstract ab ON p.paper_id = ab.paper_id
            WHERE p.paper_id = %s
        """, [paper_id])

        row = dictfetchall(cursor)
        if not row:
            return JsonResponse({"error": "not found"}, status=404)

    return JsonResponse(row[0])
