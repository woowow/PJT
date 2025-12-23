import os
import json
import time
import psycopg2
from psycopg2.extras import execute_batch

# ===============================
# DB CONFIG
# ===============================
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "paper_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
    "host": os.getenv("DB_HOST", "postgres"),
    "port": os.getenv("DB_PORT", "5432"),
}

DATA_DIR = "./data"

# ===============================
# PostgreSQL 연결 (재시도 포함)
# ===============================
def connect():
    for i in range(20):
        try:
            return psycopg2.connect(**DB_CONFIG)
        except Exception:
            print(f"⏳ DB 대기 중... ({i+1}/20)")
            time.sleep(2)
    raise Exception("❌ PostgreSQL 연결 실패")


# ===============================
# JSON 로드 (안전 버전)
# - 파일 없으면 []
# - 0바이트/깨진 JSON이면 []
# ===============================
def load_json(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return []

    try:
        # 0바이트 방어
        if os.path.getsize(path) == 0:
            print(f"⚠️ {filename} is empty file -> treated as []")
            return []

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 배열/리스트가 아니면 방어적으로 []
        if not isinstance(data, list):
            print(f"⚠️ {filename} is not a JSON list -> treated as []")
            return []
        return data

    except json.JSONDecodeError:
        print(f"⚠️ {filename} JSONDecodeError -> treated as []")
        return []
    except Exception as e:
        print(f"⚠️ {filename} load failed ({e}) -> treated as []")
        return []


# ===============================
# INSERT CATEGORY
# ===============================
def insert_category(cur, items):
    if not items:
        return

    print("📁 카테고리 처리...")

    sql = """
        INSERT INTO category (category_id, category_name, alex_category_id)
        VALUES (%s, %s, %s)
        ON CONFLICT (alex_category_id) DO UPDATE
        SET category_name = EXCLUDED.category_name;
    """

    data = [(c["category_id"], c["category_name"], c["alex_category_id"]) for c in items]
    execute_batch(cur, sql, data)


# ===============================
# INSERT INSTITUTION
# ===============================
def insert_institution(cur, items):
    if not items:
        return

    print("🏢 기관 처리...")

    sql = """
        INSERT INTO institution (institution_id, institution_name, country_code, alex_institution_id)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (alex_institution_id) DO UPDATE
        SET institution_name = EXCLUDED.institution_name,
            country_code = EXCLUDED.country_code;
    """

    data = [
        (i["institution_id"], i["institution_name"], i["country_code"], i["alex_institution_id"])
        for i in items
    ]
    execute_batch(cur, sql, data)


# ===============================
# 도우미: alex_id → 내부 PK 변환
# ===============================
def get_category_id(cur, alex_id):
    cur.execute("SELECT category_id FROM category WHERE alex_category_id=%s", (alex_id,))
    row = cur.fetchone()
    return row[0] if row else None

def get_institution_id(cur, alex_id):
    cur.execute("SELECT institution_id FROM institution WHERE alex_institution_id=%s", (alex_id,))
    row = cur.fetchone()
    return row[0] if row else None

def get_author_id(cur, alex_id):
    cur.execute("SELECT author_id FROM author WHERE alex_author_id=%s", (alex_id,))
    row = cur.fetchone()
    return row[0] if row else None

def get_paper_id(cur, alex_paper_id):
    cur.execute("SELECT paper_id FROM paper WHERE alex_paper_id=%s", (alex_paper_id,))
    row = cur.fetchone()
    return row[0] if row else None

def get_guest_id(cur, guestname):
    cur.execute("SELECT guest_id FROM guest WHERE guestname=%s", (guestname,))
    row = cur.fetchone()
    return row[0] if row else None


# ===============================
# INSERT AUTHOR
# ===============================
def insert_author(cur, items):
    if not items:
        return

    print("👤 저자 처리...")

    sql = """
        INSERT INTO author (author_id, author_name, alex_author_id,
                            institution_id, citation_total, main_topic_1, main_topic_2, main_topic_3)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (alex_author_id) DO UPDATE
        SET author_name = EXCLUDED.author_name,
            institution_id = EXCLUDED.institution_id,
            citation_total = EXCLUDED.citation_total,
            main_topic_1 = EXCLUDED.main_topic_1,
            main_topic_2 = EXCLUDED.main_topic_2,
            main_topic_3 = EXCLUDED.main_topic_3;
    """

    data = [
        (
            a.get("author_id"),
            a["author_name"],
            a["alex_author_id"],
            a.get("institution_id"),
            a.get("citation_total", None),
            a.get("main_topic_1"),
            a.get("main_topic_2"),
            a.get("main_topic_3"),
        )
        for a in items
    ]
    execute_batch(cur, sql, data)


# ===============================
# INSERT PAPER (abstract + yearcitation 포함)
# ===============================
def insert_paper(cur, items):
    if not items:
        return

    print("📄 논문 처리...")

    sql_paper = """
        INSERT INTO paper (title, category_id, institution_id, citation,
                           open_access, locations, announcement_date, submit,
                           alex_paper_id)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (alex_paper_id) DO UPDATE
        SET title = EXCLUDED.title,
            category_id = EXCLUDED.category_id,
            institution_id = EXCLUDED.institution_id,
            citation = EXCLUDED.citation,
            open_access = EXCLUDED.open_access,
            locations = EXCLUDED.locations,
            announcement_date = EXCLUDED.announcement_date,
            submit = EXCLUDED.submit;
    """

    for p in items:
        category_id = get_category_id(cur, p["category_alex_id"]) if p.get("category_alex_id") else None
        institution_id = get_institution_id(cur, p["institution_alex_id"]) if p.get("institution_alex_id") else None

        execute_batch(
            cur,
            sql_paper,
            [
                (
                    p["title"],
                    category_id,
                    institution_id,
                    p.get("citation", None),
                    p.get("open_access", False),
                    p.get("locations"),
                    p.get("announcement_date"),
                    p.get("submit"),
                    p["alex_paper_id"],
                )
            ],
        )

        # -------------------
        # ABSTRACT 저장
        # -------------------
        if p.get("abstract"):
            pid = get_paper_id(cur, p["alex_paper_id"])
            if pid:
                cur.execute(
                    """
                    INSERT INTO abstract (paper_id, context)
                    VALUES (%s, %s)
                    ON CONFLICT (paper_id) DO UPDATE
                    SET context = EXCLUDED.context;
                """,
                    (pid, p["abstract"]),
                )

        # -------------------
        # YEAR-CITATION 저장
        # -------------------
        if p.get("cited_by_year"):
            pid = get_paper_id(cur, p["alex_paper_id"])
            if pid:
                y = sorted(p["cited_by_year"], key=lambda x: -x["year"])
                counts = [y[i]["count"] if i < len(y) else 0 for i in range(3)]

                cur.execute(
                    """
                    INSERT INTO yearcitation (paper_id, recent_year1_count, recent_year2_count, recent_year3_count)
                    VALUES (%s,%s,%s,%s)
                    ON CONFLICT (paper_id) DO UPDATE
                    SET recent_year1_count = EXCLUDED.recent_year1_count,
                        recent_year2_count = EXCLUDED.recent_year2_count,
                        recent_year3_count = EXCLUDED.recent_year3_count;
                """,
                    (pid, counts[0], counts[1], counts[2]),
                )


# ===============================
# INSERT AUTHOR–PAPER RELATION
# ===============================
def insert_authorpaper(cur, items):
    if not items:
        return

    print("🔗 저자-논문 관계 처리...")

    sql = """
        INSERT INTO authorpaper (paper_id, author_id)
        VALUES (%s, %s)
        ON CONFLICT (paper_id, author_id) DO NOTHING;
    """

    data = []
    for rel in items:
        pid = get_paper_id(cur, rel["alex_paper_id"])
        aid = get_author_id(cur, rel["alex_author_id"])
        if pid and aid:
            data.append((pid, aid))

    if data:
        execute_batch(cur, sql, data)


# ===============================
# INSERT GUEST
# ===============================
def insert_guest(cur, items):
    if not items:
        return

    print("👥 GUEST 처리...")

    sql = """
        INSERT INTO guest (guest_id, guestname, pwd, interest_1, interest_2, interest_3)
        VALUES (%s,%s,%s,%s,%s,%s)
        ON CONFLICT (guestname) DO UPDATE
        SET pwd = EXCLUDED.pwd,
            interest_1 = EXCLUDED.interest_1,
            interest_2 = EXCLUDED.interest_2,
            interest_3 = EXCLUDED.interest_3;
    """

    data = [
        (
            g.get("guest_id"),
            g["guestname"],
            g["pwd"],
            g.get("interest_1"),
            g.get("interest_2"),
            g.get("interest_3"),
        )
        for g in items
    ]
    execute_batch(cur, sql, data)


# ===============================
# INSERT GUEST FAVORITE
# ===============================
def insert_guestfavorite(cur, items):
    if not items:
        return

    print("⭐ GUEST FAVORITE 처리...")

    sql = """
        INSERT INTO guestfavorite (guest_id, paper_id)
        VALUES (%s, %s)
        ON CONFLICT (guest_id, paper_id) DO NOTHING;
    """

    data = []
    for f in items:
        gid = get_guest_id(cur, f["guestname"])
        pid = get_paper_id(cur, f["alex_paper_id"])
        if gid and pid:
            data.append((gid, pid))

    if data:
        execute_batch(cur, sql, data)


# ===============================
# INSERT GUEST CATEGORY COUNT
# ===============================
def insert_guestcategory(cur, items):
    if not items:
        return

    print("📊 GUEST CATEGORY COUNT 처리...")

    # table_schema.sql 기준: 컬럼명이 count
    sql = """
        INSERT INTO guestcategorycount (guest_id, category_id, count)
        VALUES (%s, %s, %s)
        ON CONFLICT (guest_id, category_id) DO UPDATE
        SET count = EXCLUDED.count;
    """

    data = []
    for c in items:
        gid = get_guest_id(cur, c["guestname"])
        cid = get_category_id(cur, c["alex_category_id"])
        if gid and cid:
            data.append((gid, cid, c.get("count", 0)))

    if data:
        execute_batch(cur, sql, data)


# ===============================
# MAIN
# ===============================
def main():
    print("🔄 JSON → PostgreSQL 병합 시작")

    conn = connect()
    cur = conn.cursor()

    insert_category(cur, load_json("category.json"))
    insert_institution(cur, load_json("institution.json"))
    insert_author(cur, load_json("author.json"))
    insert_paper(cur, load_json("paper.json"))
    insert_authorpaper(cur, load_json("authorpaper.json"))
    insert_guest(cur, load_json("guest.json"))
    insert_guestfavorite(cur, load_json("guestfavorite.json"))
    insert_guestcategory(cur, load_json("guestcategorycount.json"))

    conn.commit()
    cur.close()
    conn.close()

    print("🎉 DB 최신화 완료!")


if __name__ == "__main__":
    main()
