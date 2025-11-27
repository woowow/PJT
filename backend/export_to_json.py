import os
import json
import psycopg2
from datetime import datetime

DB_CONFIG = {
    "dbname": "paper_db",
    "user": "postgres",
    "password": "postgres",
    "host": "postgres",
    "port": "5432"
}

EXPORT_DIR = "./data"
os.makedirs(EXPORT_DIR, exist_ok=True)


def connect():
    return psycopg2.connect(**DB_CONFIG)


def export_category(cur):
    cur.execute("SELECT category_id, category_name, alex_category_id FROM category;")
    rows = cur.fetchall()

    data = [
        {
            "category_id": r[0],
            "category_name": r[1],
            "alex_category_id": r[2]
        }
        for r in rows
    ]

    save_json("category.json", data)


def export_institution(cur):
    cur.execute("SELECT institution_id, institution_name, country_code, alex_institution_id FROM institution;")
    rows = cur.fetchall()

    data = [
        {
            "institution_id": r[0],
            "institution_name": r[1],
            "country_code": r[2],
            "alex_institution_id": r[3]
        }
        for r in rows
    ]

    save_json("institution.json", data)


def export_author(cur):
    cur.execute("""
        SELECT author_id, author_name, alex_author_id,
               institution_id, citation_total, main_topic_1, main_topic_2, main_topic_3
        FROM author;
    """)
    rows = cur.fetchall()

    data = [
        {
            "author_id": r[0],
            "author_name": r[1],
            "alex_author_id": r[2],
            "institution_id": r[3],
            "citation_total": r[4],
            "main_topic_1": r[5],
            "main_topic_2": r[6],
            "main_topic_3": r[7]
        }
        for r in rows
    ]

    save_json("author.json", data)


def export_paper(cur):
    # paper 기본 정보
    cur.execute("""
        SELECT paper_id, title, category_id, institution_id, citation,
               open_access, locations, announcement_date, submit, alex_paper_id
        FROM paper;
    """)
    papers = cur.fetchall()

    # abstract
    cur.execute("SELECT paper_id, context FROM abstract;")
    abstracts = {r[0]: r[1] for r in cur.fetchall()}

    # yearcitation
    cur.execute("""
        SELECT paper_id, recent_year1_count, recent_year2_count, recent_year3_count
        FROM yearcitation;
    """)
    citations = {
        r[0]: [r[1], r[2], r[3]]
        for r in cur.fetchall()
    }

    # category, institution 매핑
    cur.execute("SELECT category_id, alex_category_id FROM category;")
    category_map = {r[0]: r[1] for r in cur.fetchall()}

    cur.execute("SELECT institution_id, alex_institution_id FROM institution;")
    inst_map = {r[0]: r[1] for r in cur.fetchall()}

    result = []
    for p in papers:
        pid = p[0]
        title = p[1]

        result.append({
            "title": title,
            "alex_paper_id": p[9],
            "category_alex_id": category_map.get(p[2]),
            "institution_alex_id": inst_map.get(p[3]),
            "citation": p[4],
            "open_access": p[5],
            "locations": p[6],
            "announcement_date": p[7].strftime("%Y-%m-%d") if p[7] else None,
            "submit": p[8],

            # abstract 포함
            "abstract": abstracts.get(pid),

            # 최근 3년 cited_by_year 포함
            "cited_by_year": [
                {"year": 2023, "count": citations.get(pid, [0, 0, 0])[0]},
                {"year": 2022, "count": citations.get(pid, [0, 0, 0])[1]},
                {"year": 2021, "count": citations.get(pid, [0, 0, 0])[2]}
            ]
        })

    save_json("paper.json", result)


def export_authorpaper(cur):
    cur.execute("SELECT paper_id, author_id FROM authorpaper;")
    rows = cur.fetchall()

    # paper_id → alex_paper_id
    cur.execute("SELECT paper_id, alex_paper_id FROM paper;")
    paper_map = {r[0]: r[1] for r in cur.fetchall()}

    # author_id → alex_author_id
    cur.execute("SELECT author_id, alex_author_id FROM author;")
    author_map = {r[0]: r[1] for r in cur.fetchall()}

    data = []
    for p, a in rows:
        data.append({
            "alex_paper_id": paper_map.get(p),
            "alex_author_id": author_map.get(a)
        })

    save_json("authorpaper.json", data)


def export_guest(cur):
    cur.execute("SELECT guest_id, guestname, pwd, interest_1, interest_2, interest_3 FROM guest;")
    rows = cur.fetchall()

    data = [
        {
            "guest_id": r[0],
            "guestname": r[1],
            "pwd": r[2],
            "interest_1": r[3],
            "interest_2": r[4],
            "interest_3": r[5]
        }
        for r in rows
    ]

    save_json("guest.json", data)


def export_guestfavorite(cur):
    cur.execute("SELECT guest_id, paper_id FROM guestfavorite;")
    rows = cur.fetchall()

    # 매핑
    cur.execute("SELECT guest_id, guestname FROM guest;")
    gmap = {r[0]: r[1] for r in cur.fetchall()}

    cur.execute("SELECT paper_id, alex_paper_id FROM paper;")
    pmap = {r[0]: r[1] for r in cur.fetchall()}

    data = [
        {"guestname": gmap[r[0]], "alex_paper_id": pmap[r[1]]}
        for r in rows
    ]

    save_json("guestfavorite.json", data)


def export_guestcategorycount(cur):
    cur.execute("SELECT guest_id, category_id, count FROM guestcategorycount;")
    rows = cur.fetchall()

    cur.execute("SELECT guest_id, guestname FROM guest;")
    guest_map = {r[0]: r[1] for r in cur.fetchall()}

    cur.execute("SELECT category_id, alex_category_id FROM category;")
    cate_map = {r[0]: r[1] for r in cur.fetchall()}

    data = [
        {
            "guestname": guest_map[r[0]],
            "alex_category_id": cate_map[r[1]],
            "count": r[2]
        }
        for r in rows
    ]

    save_json("guestcategorycount.json", data)


def save_json(name, data):
    path = f"{EXPORT_DIR}/{name}"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ saved → {path} ({len(data)} rows)")


def main():
    conn = connect()
    cur = conn.cursor()

    export_category(cur)
    export_institution(cur)
    export_author(cur)
    export_paper(cur)                # abstract + yearcitation 포함
    export_authorpaper(cur)
    export_guest(cur)
    export_guestfavorite(cur)
    export_guestcategorycount(cur)

    cur.close()
    conn.close()
    print("\n🎉 ALL EXPORT DONE!\n")


if __name__ == "__main__":
    main()
