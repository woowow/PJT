from elasticsearch import Elasticsearch, helpers
import psycopg2

# ======================
# Elasticsearch 연결
# ======================
es = Elasticsearch("http://elasticsearch:9200")

# ======================
# PostgreSQL 연결
# ======================
conn = psycopg2.connect(
    host="paper_postgres",
    dbname="paper_db",
    user="postgres",
    password="postgres"
)

cur = conn.cursor()

# ======================
# 논문 + 대표 저자 + 메타 정보
# ======================
cur.execute("""
    SELECT
        p.paper_id AS id,
        p.title,
        STRING_AGG(a.author_name, ', ') AS author,
        MIN(a.author_id) AS author_id,
        EXTRACT(YEAR FROM p.announcement_date) AS year,
        p.citation,
        i.institution_name AS institution,
        c.category_name AS subject,
        i.country_code AS country
    FROM paper p
    LEFT JOIN authorpaper ap ON p.paper_id = ap.paper_id
    LEFT JOIN author a ON ap.author_id = a.author_id
    LEFT JOIN institution i ON p.institution_id = i.institution_id
    LEFT JOIN category c ON p.category_id = c.category_id
    GROUP BY
        p.paper_id,
        p.title,
        p.announcement_date,
        p.citation,
        i.institution_name,
        c.category_name,
        i.country_code
""")

rows = cur.fetchall()
cols = [d[0] for d in cur.description]

actions = []

for row in rows:
    doc = dict(zip(cols, row))
    actions.append({
        "_index": "papers",
        "_id": doc["id"],
        "_source": doc
    })

helpers.bulk(es, actions)

print(f"indexed {len(actions)} papers")

cur.close()
conn.close()
