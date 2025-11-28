from api_call import pipeline
import requests, time, datetime


def get_pub_year(work):
    pub = work.get("publication_date")
    if not pub:
        return None
    try:
        return int(pub[:4])
    except:
        return None


def get_bucket(year):
    if year is None:
        return None
    if year <= 2010:
        return 1
    elif 2011 <= year <= 2015:
        return 2
    elif 2016 <= year <= 2020:
        return 3
    elif 2021 <= year <= 2025:
        return 4
    return None


def fetch_level1():
    url = "https://api.openalex.org/concepts?filter=level:1&per-page=200"
    res = []
    while url:
        data = requests.get(url).json()
        res.extend(data["results"])
        url = data["meta"].get("next_url")
    return res


def fetch_works_by_category(cid):
    base = f"concepts.id:{cid}"

    url = (
        f"https://api.openalex.org/works?filter={base}"
        "&sort=cited_by_count:desc"
        "&per-page=200"
    )

    papers = []
    next_url = url

    while next_url and len(papers) < 1000:
        data = requests.get(next_url).json()
        papers.extend(data.get("results", []))
        next_url = data.get("meta", {}).get("next_url")
        time.sleep(0.12)

    # -----------------------------
    # 구간별 분류
    # -----------------------------
    buckets = {1: [], 2: [], 3: [], 4: []}

    for w in papers:
        year = get_pub_year(w)
        b = get_bucket(year)
        if b:
            buckets[b].append(w)

    # -----------------------------
    # 구간별 인용순 상위 20
    # -----------------------------
    final = []

    for b in [1, 2, 3, 4]:
        sorted_bucket = sorted(
            buckets[b],
            key=lambda w: w.get("cited_by_count", 0),
            reverse=True
        )
        final.extend(sorted_bucket[:20])

    return final



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
            raw_id = w.get("id")
            if not raw_id or not isinstance(raw_id, str):
                continue

            parts = raw_id.split("/")
            if len(parts) == 0 or "W" not in parts[-1]:
                continue

            wid = parts[-1].replace("W", "")

            # LEVEL1 정확 매칭
            level1_ids = [
                cc["id"].split("/")[-1]
                for cc in w.get("concepts", [])
                if cc.get("level") == 1 and cc.get("id")
            ]

            if cid not in level1_ids:
                continue

            try:
                pipeline(wid)
            except Exception as e:
                print(f"❌ ERROR {wid}:", e)

            time.sleep(0.1)


if __name__ == "__main__":
    run_all()
