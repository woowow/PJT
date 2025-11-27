import os
import json
import psycopg2
from psycopg2.extras import execute_batch

DATA_DIR = "./data"

DB_CONFIG = {
    "dbname": "paper_db",
    "user": "postgres",
    "password": "postgres",
    "host": "postgres",
    "port": "5432"
}

def load_json_files(prefix):
    items = []
    for file in os.listdir(DATA_DIR):
        if file.startswith(prefix) and file.endswith(".json"):
            with open(os.path.join(DATA_DIR, file), "r", encoding="utf-8") as f:
                items.extend(json.load(f))
    return items


def connect():
    return psycopg2.connect(**DB_CONFIG)



# =========================================================
# INSERT FUNCTIONS
# =========================================================

def insert_categories(cur, items):
    sql = """
        INSERT INTO category (category_name, alex_category_id)
        VALUES (%s, %s)
        ON CONFLICT (alex_category_id) DO UPDATE
        SET category_name = EXCLUDED.category_name;
    """
    data = [(i["category_name"], i["alex_category_id"]) for i in items]
    execute_batch(cur, sql, data)



def insert_institutions(cur, items):
    sql = """
        INSERT INTO institution (institution_name, country_code, alex_institution_id)
        VALUES (%s, %s, %s)
        ON CONFLICT (alex_institution_id) DO UPDATE
        SET institution_name = EXCLUDED.institution_name,
            country_code = EXCLUDED.country_code;
    """
    data = [(i["institution_name"], i["country_code"], i["alex_institution_id"]) for i in items]
    execute_batch(cur, sql, data)



def insert_authors(cur, items):
    sql = """
        INSERT INTO author 
        (author_name, alex_author_id, institution_id,
         citation_total, main_topic_1, main_topic_2, main_topic_3)
        VALUES (
            %s, %s,
            (SELECT institution_id FROM institution WHERE alex_institution_id = %s),
            %s, %s, %s, %s
        )
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
            a["author_name"], a["alex_author_id"], a["institution_alex_id"],
            a.get("citation_total", 0),
            a.get("main_topic_1"), a.get("main_topic_2"), a.get("main_topic_3")
        )
        for a in items
    ]
    execute_batch(cur, sql, data)



def insert_papers(cur, items):
    sql = """
        INSERT INTO paper 
        (title, category_id, institution_id, citation, open_access,
         locations, announcement_date, submit, alex_paper_id)
        VALUES (
            %s,
            (SELECT category_id FROM category WHERE alex_category_id = %s),
            (SELECT institution_id FROM institution WHERE alex_institution_id = %s),
            %s, %s, %s, %s, %s, %s
        )
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

    data = [
        (
            p["title"], p["category_alex_id"], p["institution_alex_id"],
            p.get("citation", 0),
            p.get("open_access", False),
            p.get("locations"),
            p.get("announcement_date"),
            p.get("submit"),
            p["alex_paper_id"]
        )
        for p in items
    ]

    execute_batch(cur, sql, data)



def insert_abstract(cur, items):
    sql = """
        INSERT INTO abstract (paper_id, context)
        VALUES (
            (SELECT paper_id FROM paper WHERE alex_paper_id = %s),
            %s
        )
        ON CONFLICT (paper_id) DO UPDATE
        SET context = EXCLUDED.context;
    """

    data = [
        (p["alex_paper_id"], p.get("abstract", None))
        for p in items if "abstract" in p
    ]
    execute_batch(cur, sql, data)



def insert_yearcitation(cur, items):
    sql = """
        INSERT INTO yearcitation
        (paper_id, recent_year1_count, recent_year2_count, recent_year3_count)
        VALUES (
            (SELECT paper_id FROM paper WHERE alex_paper_id = %s),
            %s, %s, %s
        )
        ON CONFLICT (paper_id) DO UPDATE
        SET recent_year1_count = EXCLUDED.recent_year1_count,
            recent_year2_count = EXCLUDED.recent_year2_count,
            recent_year3_count = EXCLUDED.recent_year3_count;
    """

    def extract_year_counts(cited):
        if not cited:
            return (0, 0, 0)

        cited_sorted = sorted(cited, key=lambda x: x["year"], reverse=True)
        counts = [cited_sorted[i]["count"] if i < len(cited_sorted) else 0 for i in range(3)]
        return counts[0], counts[1], counts[2]

    data = [
        (p["alex_paper_id"], *extract_year_counts(p.get("cited_by_year")))
        for p in items
    ]

    execute_batch(cur, sql, data)



def insert_authorpaper(cur, items):
    sql = """
        INSERT INTO authorpaper (paper_id, author_id)
        VALUES (
            (SELECT paper_id FROM paper WHERE alex_paper_id = %s),
            (SELECT author_id FROM author WHERE alex_author_id = %s)
        )
        ON CONFLICT DO NOTHING;
    """
    data = [(a["alex_paper_id"], a["alex_author_id"]) for a in items]
    execute_batch(cur, sql, data)



def insert_guest(cur, items):
    sql = """
        INSERT INTO guest (guestname, pwd, interest_1, interest_2, interest_3)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (guestname) DO UPDATE
        SET pwd = EXCLUDED.pwd,
            interest_1 = EXCLUDED.interest_1,
            interest_2 = EXCLUDED.interest_2,
            interest_3 = EXCLUDED.interest_3;
    """
    data = [
        (g["guestname"], g["pwd"], g.get("interest_1"), g.get("interest_2"), g.get("interest_3"))
        for g in items
    ]
    execute_batch(cur, sql, data)



def insert_guestfavorite(cur, items):
    sql = """
        INSERT INTO guestfavorite (guest_id, paper_id)
        VALUES (
            (SELECT guest_id FROM guest WHERE guestname = %s),
            (SELECT paper_id FROM paper WHERE alex_paper_id = %s)
        )
        ON CONFLICT DO NOTHING;
    """
    data = [(g["guestname"], g["alex_paper_id"]) for g in items]
    execute_batch(cur, sql, data)



def insert_guestcategorycount(cur, items):
    sql = """
        INSERT INTO guestcategorycount (guest_id, category_id, count)
        VALUES (
            (SELECT guest_id FROM guest WHERE guestname = %s),
            (SELECT category_id FROM category WHERE alex_category_id = %s),
            %s
        )
        ON CONFLICT (guest_id, category_id) DO UPDATE
        SET count = EXCLUDED.count;
    """
    data = [(g["guestname"], g["alex_category_id"], g["count"]) for g in items]
    execute_batch(cur, sql, data)



# =========================================================
# MAIN
# =========================================================

def main():
    print("🔄 JSON 데이터 → PostgreSQL 자동 병합 시작")

    conn = connect()
    cur = conn.cursor()

    categories = load_json_files("categories_")
    institutions = load_json_files("institutions_")
    authors = load_json_files("authors_")
    papers = load_json_files("papers_")
    relations = load_json_files("authorpaper_")

    guests = load_json_files("guest_")
    guestfav = load_json_files("guestfavorite_")
    guestcc = load_json_files("guestcategorycount_")

    print(f"📁 카테고리: {len(categories)}개")
    print(f"📁 기관: {len(institutions)}개")
    print(f"📁 저자: {len(authors)}개")
    print(f"📁 논문: {len(papers)}개")
    print(f"📁 관계: {len(relations)}개")
    print(f"📁 guest: {len(guests)}개")
    print(f"📁 즐겨찾기: {len(guestfav)}개")
    print(f"📁 guest-category-count: {len(guestcc)}개")

    insert_categories(cur, categories)
    insert_institutions(cur, institutions)
    insert_authors(cur, authors)
    insert_papers(cur, papers)
    insert_abstract(cur, papers)
    insert_yearcitation(cur, papers)
    insert_authorpaper(cur, relations)

    insert_guest(cur, guests)
    insert_guestfavorite(cur, guestfav)
    insert_guestcategorycount(cur, guestcc)

    conn.commit()
    cur.close()
    conn.close()

    print("✅ DB 최신 업데이트 완료")



if __name__ == "__main__":
    main()
