from api_call import pipeline
import requests
import time


# ------------------------------
# 설정값
# ------------------------------
PER_FIELD_LIMIT = 50  # "하나의 필드(=Level1 카테고리)당" 최종 적재할 논문 수

# (요청 기준 1) 연도 구간별 최신 논문
YEAR_BUCKETS = [
    (2021, 2025),  # 2025 ~ 2021
    (2016, 2020),  # 2020 ~ 2016
    (2011, 2015),  # 2015 ~ 2011
    (2006, 2010)  # 2010 ~ 2006
]
PER_BUCKET_LIMIT = 5  # 각 구간에서 뽑을 논문 수

# (요청 기준 2) 인용수 내림차순
TOP_CITED_LIMIT = 30


# ------------------------------
# 공통 HTTP fetch (next_url / cursor paging)
# ------------------------------
def _fetch_results(url, limit):
    results = []
    while url and len(results) < limit:
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"❌ OpenAlex 요청 실패: {e} / url={url}")
            break

        page_results = data.get("results", [])
        results.extend(page_results)

        # works endpoint는 meta.next_url을 제공
        url = (data.get("meta") or {}).get("next_url")
        time.sleep(0.15)

    return results[:limit]


# ------------------------------
# LEVEL 1 카테고리 전체 가져오기 (cursor 기반)
# ------------------------------
def fetch_level1():
    url = "https://api.openalex.org/concepts?filter=level:1&per-page=200&cursor=*"
    res = []
    page = 1

    while url:
        print(f"📡 Fetching Level1 page {page} ...")
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"❌ Level1 fetch 실패: {e} / url={url}")
            break

        if "results" not in data:
            print("❌ Unexpected API response:", data)
            break

        res.extend(data["results"])
        url = (data.get("meta") or {}).get("next_cursor")
        if url:
            url = f"https://api.openalex.org/concepts?filter=level:1&per-page=200&cursor={url}"

        page += 1
        time.sleep(0.15)

    print(f"✅ Level1 categories fetched: {len(res)}")
    return res


# ------------------------------
# (기준 1) 연도 구간별 최신 논문(출판일 최신순) 가져오기
# ------------------------------
def fetch_works_by_category_year_buckets(cid, buckets=YEAR_BUCKETS, per_bucket=PER_BUCKET_LIMIT):
    papers = []
    for (start_year, end_year) in buckets:
        from_date = f"{start_year}-01-01"
        to_date = f"{end_year}-12-31"

        url = (
            "https://api.openalex.org/works?"
            f"filter=concepts.id:{cid},from_publication_date:{from_date},to_publication_date:{to_date}"
            f"&per-page=200&sort=publication_date:desc"
        )

        bucket_papers = _fetch_results(url, per_bucket)
        papers.extend(bucket_papers)

    return papers


# ------------------------------
# (기준 2) 인용수 내림차순 논문 가져오기
# ------------------------------
def fetch_works_by_category_top_cited(cid, limit=TOP_CITED_LIMIT):
    url = (
        "https://api.openalex.org/works?"
        f"filter=concepts.id:{cid}"
        f"&per-page=200&sort=cited_by_count:desc"
    )
    return _fetch_results(url, limit)


# ------------------------------
# 두 기준을 합쳐 "필드당 50개"로 정리
# ------------------------------
def select_works_for_category(cid):
    # 1) 연도 구간별 최신 논문 (최대 5*15=75개가 될 수 있음)
    by_year = fetch_works_by_category_year_buckets(cid)

    # 2) 인용수 상위 30개
    by_cite = fetch_works_by_category_top_cited(cid)

    # 3) 합치고 중복 제거 후 50개로 컷
    selected = []
    seen = set()

    def _push(work):
        raw_id = work.get("id")
        if not raw_id or not isinstance(raw_id, str):
            return
        if raw_id in seen:
            return
        seen.add(raw_id)
        selected.append(work)

    # 우선순위: (기준1) → (기준2)
    for w in by_year:
        _push(w)
        if len(selected) >= PER_FIELD_LIMIT:
            return selected[:PER_FIELD_LIMIT]

    for w in by_cite:
        _push(w)
        if len(selected) >= PER_FIELD_LIMIT:
            break

    return selected[:PER_FIELD_LIMIT]


# ------------------------------
# 전체 실행
# ------------------------------
def run_all():
    level1 = fetch_level1()

    for c in level1:
        cid = c.get("id", "").split("/")[-1]
        cname = c.get("display_name", "Unknown")

        print("\n===============================")
        print(f"📌 LEVEL_1 : {cname} (ID={cid})")
        print("===============================")

        papers = select_works_for_category(cid)

        for w in papers:
            raw_id = w.get("id")

            # ID가 없으면 skip
            if not raw_id or not isinstance(raw_id, str):
                print("❌ ERROR: Work has no valid ID → skipped")
                continue

            # W123 형태만 허용
            parts = raw_id.split("/")
            if len(parts) == 0 or "W" not in parts[-1]:
                print("❌ ERROR: Work ID format invalid → skipped")
                continue

            wid = parts[-1].replace("W", "")

            # LEVEL1 정확 매칭 필터(안전장치)
            level1_ids = []
            for cc in w.get("concepts", []):
                if cc.get("level") == 1 and cc.get("id"):
                    level1_ids.append(cc["id"].split("/")[-1])

            if cid not in level1_ids:
                continue

            # pipeline 실행 (현재 Level1 concept를 강제로 category로 사용)
            try:
                pipeline(wid)
            except Exception as e:
                print(f"❌ ERROR {wid}:", e)

            time.sleep(0.1)


if __name__ == "__main__":
    run_all()
