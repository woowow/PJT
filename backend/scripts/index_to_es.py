from elasticsearch import Elasticsearch, helpers
import psycopg2
from psycopg2.extras import RealDictCursor
import argparse

INDEX_NAME = "papers"

def make_es():
    # 둘 다 시도 (환경 따라 서비스명/컨테이너명이 다르게 먹을 수 있음)
    for url in ["http://paper_elasticsearch:9200", "http://elasticsearch:9200", "http://localhost:9200"]:
        try:
            es = Elasticsearch(url)
            es.info()
            print(f"[ES] connected: {url}")
            return es
        except Exception:
            pass
    raise RuntimeError("Cannot connect to Elasticsearch")

def make_db():
    # 너 docker-compose 기준으로는 paper_postgres가 확실
    return psycopg2.connect(
        host="paper_postgres",
        dbname="paper_db",
        user="postgres",
        password="postgres",
    )

def ensure_index(es: Elasticsearch, recreate: bool):
    if recreate and es.indices.exists(index=INDEX_NAME):
        print(f"[ES] delete index: {INDEX_NAME}")
        es.indices.delete(index=INDEX_NAME)

    if not es.indices.exists(index=INDEX_NAME):
        print(f"[ES] create index: {INDEX_NAME}")
        body = {
            "settings": {"number_of_shards": 1, "number_of_replicas": 1},
            "mappings": {
                "properties": {
                    "id": {"type": "integer"},
                    "title": {"type": "text"},
                    "author": {"type": "text"},
                    "author_id": {"type": "integer"},
                    "year": {"type": "integer"},
                    "citation": {"type": "integer"},
                    "institution": {"type": "text"},
                    # ✅ filter(term)용 keyword 보장
                    "subject": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                    # ✅ 국가코드는 keyword가 정답
                    "country": {"type": "keyword"},
                }
            },
        }
        es.indices.create(index=INDEX_NAME, body=body)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--recreate", action="store_true")
    parser.add_argument("--chunk", type=int, default=1000)
    args = parser.parse_args()

    es = make_es()
    conn = make_db()

    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM paper;")
        print("[DB] paper count =", cur.fetchone()[0])

    ensure_index(es, recreate=args.recreate)

    sql = """
        SELECT
            p.paper_id AS id,
            p.title,
            COALESCE(aagg.author, '') AS author,
            COALESCE(aagg.min_author_id, NULL) AS author_id,
            COALESCE(EXTRACT(YEAR FROM p.announcement_date)::int, NULL) AS year,
            COALESCE(p.citation, 0) AS citation,
            i.institution_name AS institution,
            c.category_name AS subject,
            i.country_code AS country
        FROM paper p
        LEFT JOIN institution i ON p.institution_id = i.institution_id
        LEFT JOIN category c ON p.category_id = c.category_id
        LEFT JOIN (
            SELECT
                ap.paper_id,
                STRING_AGG(a.author_name, ', ' ORDER BY a.author_name) AS author,
                MIN(a.author_id) AS min_author_id
            FROM authorpaper ap
            JOIN author a ON ap.author_id = a.author_id
            GROUP BY ap.paper_id
        ) aagg ON aagg.paper_id = p.paper_id
        ORDER BY p.paper_id ASC
    """

    actions = []
    indexed = 0

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.itersize = args.chunk
        cur.execute(sql)

        for doc in cur:
            actions.append({
                "_index": INDEX_NAME,
                "_id": str(doc["id"]),
                "_source": doc,
            })

            if len(actions) >= args.chunk:
                helpers.bulk(es, actions, refresh=False)
                indexed += len(actions)
                print(f"[ES] indexed: {indexed}")
                actions = []

        if actions:
            helpers.bulk(es, actions, refresh=False)
            indexed += len(actions)

    es.indices.refresh(index=INDEX_NAME)
    print(f"indexed {indexed} papers")

    conn.close()

if __name__ == "__main__":
    main()
