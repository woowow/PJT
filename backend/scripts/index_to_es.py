from elasticsearch import Elasticsearch
import psycopg2

es = Elasticsearch("http://elasticsearch:9200")

conn = psycopg2.connect(
    host="postgres",
    dbname="paper_db",
    user="postgres",
    password="postgres"
)

cur = conn.cursor()
cur.execute("""
    SELECT
        p.paper_id,
        p.title,
        a.author_name,
        c.category_name,
        i.country_code,
        i.institution_name,
        EXTRACT(YEAR FROM p.announcement_date),
        p.citation
    FROM paper p
    LEFT JOIN authorpaper ap ON p.paper_id = ap.paper_id
    LEFT JOIN author a ON ap.author_id = a.author_id
    LEFT JOIN category c ON p.category_id = c.category_id
    LEFT JOIN institution i ON p.institution_id = i.institution_id
""")

for row in cur.fetchall():
    es.index(
        index="papers",
        id=row[0],
        document={
            "paper_id": row[0],
            "title": row[1],
            "author": row[2],
            "category": row[3],
            "country": row[4],
            "institution": row[5],
            "year": row[6],
            "citation": row[7],
        }
    )

print("✅ Elasticsearch indexing done")
