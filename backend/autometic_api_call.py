# from api_call import pipeline
# import requests, time

# def fetch_level1():
#     url = "https://api.openalex.org/concepts?filter=level:1&per-page=50"
#     res = []
#     while url:
#         data = requests.get(url).json()
#         res.extend(data["results"])
#         url = data["meta"].get("next_url")
#     return res


# def fetch_works_by_category(cid, limit=50):
#     url = f"https://api.openalex.org/works?filter=concepts.id:{cid}&per-page=50&sort=publication_date:desc"
#     papers = []
#     while url and len(papers) < limit:
#         data = requests.get(url).json()
#         papers.extend(data["results"])
#         url = data["meta"].get("next_url")
#         time.sleep(0.15)
#     return papers[:limit]


# def run_all():
#     level1 = fetch_level1()

#     for c in level1:
#         cid = c["id"].split("/")[-1]
#         cname = c["display_name"]

#         print("\n===============================")
#         print(f"📌 LEVEL_1 : {cname} (ID={cid})")
#         print("===============================")

#         papers = fetch_works_by_category(cid)

#         for w in papers:
#             # ------------------------------
#             # skip if work has no ID
#             # ------------------------------
#             raw_id = w.get("id")

#             if not raw_id or not isinstance(raw_id, str):
#                 print("❌ ERROR: Work has no valid ID → skipped")
#                 continue

#             # Wxxxx 형태만 수집
#             parts = raw_id.split("/")
#             if len(parts) == 0 or "W" not in parts[-1]:
#                 print("❌ ERROR: Work ID format invalid → skipped")
#                 continue

#             wid = parts[-1].replace("W", "")

#             # ------------------------------
#             # exact match for level_1 concepts
#             # ------------------------------
#             level1_ids = []
#             for cc in w.get("concepts", []):
#                 if cc.get("level") == 1 and cc.get("id"):
#                     level1_ids.append(cc["id"].split("/")[-1])

#             if cid not in level1_ids:
#                 continue

#             # ------------------------------
#             # pipeline 실행
#             # ------------------------------
#             try:
#                 pipeline(wid)
#             except Exception as e:
#                 print(f"❌ ERROR {wid}:", e)

#             time.sleep(0.1)


# if __name__ == "__main__":
#     run_all()


from api_call import pipeline
import requests, time

# ------------------------------
# LEVEL 1 카테고리 전체 284개 가져오기 (cursor 기반)
# ------------------------------
def fetch_level1():
    url = "https://api.openalex.org/concepts?filter=level:1&per-page=200&cursor=*"
    res = []
    page = 1

    while url:
        print(f"📡 Fetching Level1 page {page} ...")
        data = requests.get(url).json()

        # results가 없으면 에러 출력
        if "results" not in data:
            print("❌ Unexpected API response:", data)
            break

        res.extend(data["results"])

        next_cursor = data["meta"].get("next_cursor")
        if not next_cursor:
            break

        url = f"https://api.openalex.org/concepts?filter=level:1&per-page=200&cursor={next_cursor}"
        page += 1

    print(f"✅ TOTAL LEVEL1 CATEGORIES: {len(res)}")
    return res


# ------------------------------
# 카테고리별 논문 가져오기 (기존 방식 유지)
# ------------------------------
def fetch_works_by_category(cid, limit=50):
    url = f"https://api.openalex.org/works?filter=concepts.id:{cid}&per-page=50&sort=publication_date:desc"
    papers = []
    while url and len(papers) < limit:
        data = requests.get(url).json()
        papers.extend(data["results"])
        url = data["meta"].get("next_url")
        time.sleep(0.15)
    return papers[:limit]


# ------------------------------
# MAIN LOOP
# ------------------------------
def run_all():
    level1 = fetch_level1()   # ← 이제 284개를 가져옴

    for c in level1:
        cid = c["id"].split("/")[-1]
        cname = c["display_name"]

        print("\n===============================")
        print(f"📌 LEVEL_1 : {cname} (ID={cid})")
        print("===============================")

        papers = fetch_works_by_category(cid)

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

            # LEVEL1 정확 매칭 필터
            level1_ids = []
            for cc in w.get("concepts", []):
                if cc.get("level") == 1 and cc.get("id"):
                    level1_ids.append(cc["id"].split("/")[-1])

            if cid not in level1_ids:
                continue

            # pipeline 실행
            try:
                pipeline(wid)
            except Exception as e:
                print(f"❌ ERROR {wid}:", e)

            time.sleep(0.1)


if __name__ == "__main__":
    run_all()
