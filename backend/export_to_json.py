import os
import json
import psycopg2
from datetime import datetime

# -----------------------------
# DB 연결 설정
# - docker 내부 실행 기준: host=postgres
# - 로컬에서 실행할 수도 있으니 ENV 우선
# -----------------------------
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "paper_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
    "host": os.getenv("DB_HOST", "postgres"),
    "port": os.getenv("DB_PORT", "5432"),
}

EXPORT_DIR = "./data"
os.makedirs(EXPORT_DIR, exist_ok=True)


def connect():
    return psycopg2.connect(**DB_CONFIG)


def save_json(name, data):
    path = f"{EXPORT_DIR}/{name}"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    print(f"✅ saved → {path} ({len(data)} rows)")


# -----------------------------
# guestcategorycount counter col 자동 탐지
# -----------------------------
def get_gcc_counter_column(cur):
    cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema='public'
          AND table_name='guestcategorycount'
        ORDER BY ordinal_position
    """)
    cols = cur.fetchall()  # [(name, type), ...]

    names = {c[0] for c in cols}
    # 가장 흔한 후보 우선
    candidates = ["cnt", "count", "total_cnt", "view_count", "click_count", "read_count", "hit_count", "num"]
    for c in candidates:
        if c in names:
            return c

    # fallback: guest_id/category_id/ucc_id 제외한 integer 계열 첫 번째
    for col_name, data_type in cols:
        if col_name in {"ucc_id", "guest_id", "category_id"}:
            continue
        if data_type in {"integer", "bigint", "smallint"}:
            return col_name

    # 없으면 None
    return None


def export_category(cur):
    cur.execute("SELECT category_id, category_name, alex_category_id FROM category;")
    rows = cur.fetchall()

    data = [{"category_id": r[0], "category_name": r[1], "alex_category_id": r[2]} for r in rows]
    save_json("category.json", data)


def export_institution(cur):
    # 너의 exporter는 alex_institution_id를 쓰고 있으니 컬럼 존재 전제
    cur.execute("SELECT institution_id, institution_name, country_code, alex_institution_id FROM institution;")
    rows = cur.fetchall()

    data = [{
        "institution_id": r[0],
        "institution_name": r[1],
        "country_code": r[2],
        "alex_institution_id": r[3]
    } for r in rows]
    save_json("institution.json", data)


def export_author(cur):
    cur.execute("""
        SELECT author_id, author_name, alex_author_id,
               institution_id, citation_total, main_topic_1, main_topic_2, main_topic_3
        FROM author;
    """)
    rows = cur.fetchall()

    data = [{
        "author_id": r[0],
        "author_name": r[1],
        "alex_author_id": r[2],
        "institution_id": r[3],
        "citation_total": r[4],
        "main_topic_1": r[5],
        "main_topic_2": r[6],
        "main_topic_3": r[7],
    } for r in rows]
    save_json("author.json", data)


def export_paper(cur):
    cur.execute("""
        SELECT paper_id, title, category_id, institution_id, citation,
               open_access, locations, announcement_date, submit, alex_paper_id
        FROM paper;
    """)
    papers = cur.fetchall()

    cur.execute("SELECT paper_id, context FROM abstract;")
    abstracts = {r[0]: r[1] for r in cur.fetchall()}

    cur.execute("""
        SELECT paper_id, recent_year1_count, recent_year2_count, recent_year3_count
        FROM yearcitation;
    """)
    citations = {r[0]: [r[1], r[2], r[3]] for r in cur.fetchall()}

    cur.execute("SELECT category_id, alex_category_id FROM category;")
    category_map = {r[0]: r[1] for r in cur.fetchall()}

    cur.execute("SELECT institution_id, alex_institution_id FROM institution;")
    inst_map = {r[0]: r[1] for r in cur.fetchall()}

    result = []
    for p in papers:
        pid = p[0]
        result.append({
            "title": p[1],
            "alex_paper_id": p[9],
            "category_alex_id": category_map.get(p[2]),
            "institution_alex_id": inst_map.get(p[3]),
            "citation": p[4],
            "open_access": p[5],
            "locations": p[6],
            "announcement_date": p[7].strftime("%Y-%m-%d") if p[7] else None,
            "submit": p[8],
            "abstract": abstracts.get(pid),
            "cited_by_year": [
                {"year": 2023, "count": citations.get(pid, [0, 0, 0])[0]},
                {"year": 2022, "count": citations.get(pid, [0, 0, 0])[1]},
                {"year": 2021, "count": citations.get(pid, [0, 0, 0])[2]},
            ]
        })

    save_json("paper.json", result)


def export_authorpaper(cur):
    cur.execute("SELECT paper_id, author_id FROM authorpaper;")
    rows = cur.fetchall()

    cur.execute("SELECT paper_id, alex_paper_id FROM paper;")
    paper_map = {r[0]: r[1] for r in cur.fetchall()}

    cur.execute("SELECT author_id, alex_author_id FROM author;")
    author_map = {r[0]: r[1] for r in cur.fetchall()}

    data = [{"alex_paper_id": paper_map.get(p), "alex_author_id": author_map.get(a)} for p, a in rows]
    save_json("authorpaper.json", data)


def export_guest(cur):
    cur.execute("SELECT guest_id, guestname, pwd, interest_1, interest_2, interest_3 FROM guest;")
    rows = cur.fetchall()

    data = [{
        "guest_id": r[0],
        "guestname": r[1],
        "pwd": r[2],
        "interest_1": r[3],
        "interest_2": r[4],
        "interest_3": r[5],
    } for r in rows]
    save_json("guest.json", data)


def export_guestfavorite(cur):
    cur.execute("SELECT guest_id, paper_id FROM guestfavorite;")
    rows = cur.fetchall()

    cur.execute("SELECT guest_id, guestname FROM guest;")
    gmap = {r[0]: r[1] for r in cur.fetchall()}

    cur.execute("SELECT paper_id, alex_paper_id FROM paper;")
    pmap = {r[0]: r[1] for r in cur.fetchall()}

    data = [{"guestname": gmap[r[0]], "alex_paper_id": pmap[r[1]]} for r in rows]
    save_json("guestfavorite.json", data)


def export_guestcategorycount(cur):
    counter_col = get_gcc_counter_column(cur)
    if not counter_col:
        # 구조가 예외인 경우라도 파일은 남김(빈 배열)
        save_json("guestcategorycount.json", [])
        return

    # counter_col은 식별자라 SQL에 직접 넣어야 함 (주의: 안전하게 포맷)
    q = f"SELECT guest_id, category_id, {counter_col} FROM guestcategorycount;"
    cur.execute(q)
    rows = cur.fetchall()

    cur.execute("SELECT guest_id, guestname FROM guest;")
    guest_map = {r[0]: r[1] for r in cur.fetchall()}

    cur.execute("SELECT category_id, alex_category_id FROM category;")
    cate_map = {r[0]: r[1] for r in cur.fetchall()}

    data = [{
        "guestname": guest_map.get(r[0]),
        "alex_category_id": cate_map.get(r[1]),
        "count": r[2],
    } for r in rows]

    save_json("guestcategorycount.json", data)


# -----------------------------
# (선택) 새 테이블 export
# - 제출용은 안 해도 됨
# -----------------------------
def export_guest_recommend(cur):
    try:
        cur.execute("""
            SELECT guest_id, paper_id, score, reason, created_at
            FROM guest_recommend;
        """)
        rows = cur.fetchall()
    except Exception:
        # 테이블 없거나 아직 미생성인 경우
        save_json("guest_recommend.json", [])
        return

    data = [{
        "guest_id": r[0],
        "paper_id": r[1],
        "score": float(r[2]) if r[2] is not None else 0.0,
        "reason": r[3],
        "created_at": r[4].isoformat() if r[4] else None,
    } for r in rows]

    save_json("guest_recommend.json", data)


def export_reco_job_run(cur):
    try:
        cur.execute("""
            SELECT run_id, ran_at, status, notes
            FROM reco_job_run
            ORDER BY run_id;
        """)
        rows = cur.fetchall()
    except Exception:
        save_json("reco_job_run.json", [])
        return

    data = [{
        "run_id": r[0],
        "ran_at": r[1].isoformat() if r[1] else None,
        "status": r[2],
        "notes": r[3],
    } for r in rows]

    save_json("reco_job_run.json", data)


def main():
    conn = connect()
    cur = conn.cursor()

    export_category(cur)
    export_institution(cur)
    export_author(cur)
    export_paper(cur)
    export_authorpaper(cur)
    export_guest(cur)
    export_guestfavorite(cur)
    export_guestcategorycount(cur)

    # (선택) 새 테이블 export
    export_guest_recommend(cur)
    export_reco_job_run(cur)

    cur.close()
    conn.close()
    print("\n🎉 ALL EXPORT DONE!\n")


if __name__ == "__main__":
    main()
