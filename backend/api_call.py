import requests
import psycopg2
import json

# -----------------------------
# DB 연결
# -----------------------------
def get_conn():
    return psycopg2.connect(
        host="postgres",          # DOCKER DB SERVICE NAME
        dbname="paper_db",        # docker-compose.yml 에 설정한 DB
        user="postgres",
        password="postgres",
        port=5432
    )
# -----------------------------
# Abstract 변환 함수
# -----------------------------
def convert_abstract(inverted):
    # abstract 자체가 없는 논문이면 None 리턴
    if not inverted:
        return None

    max_pos = max(pos for positions in inverted.values() for pos in positions)
    text = [""] * (max_pos + 1)
    for word, positions in inverted.items():
        for pos in positions:
            text[pos] = word
    return " ".join(text)


# -----------------------------
# API GET Wrapper
# -----------------------------
def fetch_work(work_id):

    # ID가 None인 경우 API 자체가 불가능 → 방어 코드
    if not work_id:
        return None
    

    work_id = str(work_id).upper().replace("W", "")
    url = f"https://api.openalex.org/works/W{work_id}"
    return requests.get(url).json()

# def fetch_author(author_id):
#     url = f"https://api.openalex.org/authors/A{author_id}"
#     return requests.get(url).json()


# -----------------------------
# INSERT QUERIES
# -----------------------------

# category table
def insert_category(conn, level1):

    if not level1:
        return None
    if not level1.get("id"):
        return None

    alex_category_id = level1["id"].split("/")[-1].replace("C", "")
    category_name = level1.get("display_name", "Unknown")

    sql = """
    INSERT INTO category (category_name, alex_category_id)
    VALUES (%s, %s)
    ON CONFLICT (alex_category_id) DO UPDATE
    SET category_name = EXCLUDED.category_name
    RETURNING category_id;
    """

    with conn.cursor() as cur:
        cur.execute(sql, (category_name, alex_category_id))
        category_id = cur.fetchone()[0]
        conn.commit()

    return category_id




# institution에 넣기
def insert_institution(conn, inst):

    # inst 자체가 None이면 기관 없음 → None 리턴
    if not inst:
        return None

    # ---------------------------------------------------
    # ⭐ 방어코드 1: inst["id"]가 None / '' / 존재하지 않을 경우 대비
    # ---------------------------------------------------
    alex_inst_raw = inst.get("id")

    alex_institution_id = None
    if alex_inst_raw and isinstance(alex_inst_raw, str) and "openalex.org" in alex_inst_raw:
        # 예: https://openalex.org/I123456789 → I123456789 → 123456789
        try:
            alex_institution_id = alex_inst_raw.split("/")[-1].replace("I", "")
        except:
            alex_institution_id = None  # split 오류 방지
    # else:
    #   alex_institution_id는 None으로 그대로 둠 (DB에 NULL 저장됨)

    # ---------------------------------------------------
    # 기관명, 국가코드 추출
    # ---------------------------------------------------
    name = inst.get("display_name")
    country = inst.get("country_code")

    # ---------------------------------------------------
    # ⭐ INSERT에 alex_institution_id 포함
    #    id가 None이라도 DB에는 NULL 저장 가능
    # ---------------------------------------------------
    sql = """
        INSERT INTO institution (institution_name, country_code, alex_institution_id)
        VALUES (%s, %s, %s)
        ON CONFLICT (alex_institution_id) DO UPDATE
        SET institution_name = EXCLUDED.institution_name,
            country_code = EXCLUDED.country_code
        RETURNING institution_id;
    """

    with conn.cursor() as cur:
        cur.execute(sql, (name, country, alex_institution_id))
        new_id = cur.fetchone()[0]
        conn.commit()
        return new_id


# author table 넣기
def insert_author(conn, author_basic):

    if not author_basic:
        return None

    # author ID가 None일 수 있으므로 방어 코드 추가
    if not author_basic.get("id"):
        return None

    # Work API 안에 들어있는 저자 기본 정보만 사용
    alex_author_id = author_basic["id"].split("/")[-1].replace("A", "")
    author_name = author_basic["display_name"]

    sql = """
    INSERT INTO author (author_name, alex_author_id)
    VALUES (%s, %s)
    ON CONFLICT (alex_author_id) DO UPDATE
    SET author_name = EXCLUDED.author_name
    RETURNING author_id;
    """

    with conn.cursor() as cur:
        cur.execute(sql, (author_name, alex_author_id))
        author_id = cur.fetchone()[0]
        conn.commit()

    return author_id


def insert_paper(conn, work, category_id, institution_id):

    # work["id"]가 None이면 split() 불가능 → 방어 코드
    wid_raw = work.get("id")
    if not wid_raw:
        return None
    
    alex_paper_id = work["id"].split("/")[-1].replace("W", "")
    title = work.get("title")
    citation = work.get("cited_by_count")
    open_access = work["open_access"]["is_oa"] if work.get("open_access") else False

    # ------------------------------
    # 📌 locations → landing_page_url만 저장
    # ------------------------------
    landing_page_url = None
    if work.get("locations"):
        # 여러 location 중에서 landing_page_url 있는 첫 번째 찾기
        for loc in work["locations"]:
            if loc.get("landing_page_url"):
                landing_page_url = loc["landing_page_url"]
                break

    # DB에는 문자열만 저장
    locations = landing_page_url

    pub_date = work.get("publication_date")
    submit = work["host_venue"]["display_name"] if work.get("host_venue") else None

    sql = """
    INSERT INTO paper (title, category_id, institution_id, citation, open_access,
                       locations, announcement_date, submit, alex_paper_id, weekly_count)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 0)
    ON CONFLICT (alex_paper_id) DO UPDATE
    SET title = EXCLUDED.title
    RETURNING paper_id;
    """

    with conn.cursor() as cur:
        cur.execute(sql, (title, category_id, institution_id, citation, open_access,
                          locations, pub_date, submit, alex_paper_id))
        paper_id = cur.fetchone()[0]
        conn.commit()

    return paper_id


# abstrack에 넣기
def insert_abstract(conn, paper_id, work):
    abstract_idx = work.get("abstract_inverted_index")
    # 단순 text로 들어오지 않고, 이상하게 들어오므로, 이걸 다시 제대로 된 text로 저장
    # 메모리 차이 거의 X
    text = convert_abstract(abstract_idx)

    sql = """
    INSERT INTO abstract (paper_id, context)
    VALUES (%s, %s)
    ON CONFLICT (paper_id) DO UPDATE SET context = EXCLUDED.context;
    """

    with conn.cursor() as cur:
        cur.execute(sql, (paper_id, text))
        conn.commit()

# 연도 순서대로 정렬 / 없는 년도라면 0으로
def insert_year_citation(conn, paper_id, work):
    counts = work.get("counts_by_year", [])
    # 년도 순서대로 정렬
    counts = sorted(counts, key=lambda x: x["year"], reverse=True)

    y1 = counts[0]["cited_by_count"] if len(counts) > 0 else 0
    y2 = counts[1]["cited_by_count"] if len(counts) > 1 else 0
    y3 = counts[2]["cited_by_count"] if len(counts) > 2 else 0

    sql = """
    INSERT INTO yearcitation (paper_id, recent_year1_count, recent_year2_count, recent_year3_count)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (paper_id) DO UPDATE
    SET recent_year1_count = EXCLUDED.recent_year1_count,
        recent_year2_count = EXCLUDED.recent_year2_count,
        recent_year3_count = EXCLUDED.recent_year3_count;
    """

    with conn.cursor() as cur:
        cur.execute(sql, (paper_id, y1, y2, y3))
        conn.commit()


def insert_author_paper(conn, paper_id, author_id):
    sql = """
    INSERT INTO authorpaper (paper_id, author_id)
    VALUES (%s, %s)
    ON CONFLICT DO NOTHING;
    """
    with conn.cursor() as cur:
        cur.execute(sql, (paper_id, author_id))
        conn.commit()


# -----------------------------
# 🚀 전체 파이프라인 실행
# -----------------------------
def pipeline(work_id):
    conn = get_conn()
    work = fetch_work(work_id)
    if not work:
        print("❌ Work 데이터 없음 → skip")
        return
    
    
    # 1) 카테고리(level 1)
    concept = next((c for c in work["concepts"] if c["level"] == 1), None)

    # 1) 카테고리(level 1)
    concepts = work.get("concepts")

    if not concepts:
        concept = None
    else:
        concept = next((c for c in concepts if c and c.get("level") == 1), None)

    # category_id는 반드시 여기서 공통적으로 처리해야 함
    category_id = insert_category(conn, concept) if concept else None


    # 2) institutions (first author institution)
    authorships = work.get("authorships", [])
    inst = None
    if authorships and authorships[0]["institutions"]:
        inst = authorships[0]["institutions"][0]
        institution_id = insert_institution(conn, inst)
    else:
        institution_id = None

    # 3) paper insert
    paper_id = insert_paper(conn, work, category_id, institution_id)

    # 4) abstract
    insert_abstract(conn, paper_id, work)

    # 5) year citation
    insert_year_citation(conn, paper_id, work)

    # 6) authors & author_paper
    for auth in authorships:
        author_basic = auth.get("author")

        # author 자체가 None인 경우 skip
        if not author_basic:
            continue

        author_id_raw = author_basic.get("id")

        # id가 None 또는 빈 문자열이면 skip
        if not author_id_raw:
            continue

        alex_author_id = author_id_raw.split("/")[-1].replace("A", "")
        author_name = author_basic.get("display_name")

        author_id = insert_author(conn, author_basic)
        if author_id:
            insert_author_paper(conn, paper_id, author_id)


    conn.close()

    print(f"Inserted Work {work_id} → paper_id={paper_id}")


# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    pipeline(2741809807)
