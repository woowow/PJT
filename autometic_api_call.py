from api_call import pipeline
import requests, time

def fetch_level1():
    url = "https://api.openalex.org/concepts?filter=level:1&per-page=200"
    res = []
    while url:
        data = requests.get(url).json()
        res.extend(data["results"])
        url = data["meta"].get("next_url")
    return res


def fetch_works_by_category(cid, limit=1000):
    url = f"https://api.openalex.org/works?filter=concepts.id:{cid}&per-page=200&sort=publication_date:desc"
    papers = []
    while url and len(papers) < limit:
        data = requests.get(url).json()
        papers.extend(data["results"])
        url = data["meta"].get("next_url")
        time.sleep(0.15)
    return papers[:limit]


def run_all():
    level1 = fetch_level1()

    for c in level1:
        cid = c["id"].split("/")[-1]
        cname = c["display_name"]

        print("\n===============================")
        print(f"📌 LEVEL_1 : {cname} (ID={cid})")
        print("===============================")

        papers = fetch_works_by_category(cid)

        for w in papers:
            # ------------------------------
            # skip if work has no ID
            # ------------------------------
            raw_id = w.get("id")

            if not raw_id or not isinstance(raw_id, str):
                print("❌ ERROR: Work has no valid ID → skipped")
                continue

            # Wxxxx 형태만 수집
            parts = raw_id.split("/")
            if len(parts) == 0 or "W" not in parts[-1]:
                print("❌ ERROR: Work ID format invalid → skipped")
                continue

            wid = parts[-1].replace("W", "")

            # ------------------------------
            # exact match for level_1 concepts
            # ------------------------------
            level1_ids = []
            for cc in w.get("concepts", []):
                if cc.get("level") == 1 and cc.get("id"):
                    level1_ids.append(cc["id"].split("/")[-1])

            if cid not in level1_ids:
                continue

            # ------------------------------
            # pipeline 실행
            # ------------------------------
            try:
                pipeline(wid)
            except Exception as e:
                print(f"❌ ERROR {wid}:", e)

            time.sleep(0.1)


if __name__ == "__main__":
    run_all()
