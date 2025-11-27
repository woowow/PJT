import requests
import time



def fetch_level2_concepts():
    url = "https://api.openalex.org/concepts"
    params = {
        "filter": "level:1",
        "per-page": 200,   # 한 번에 최대 가져오기
        "page": 1
    }

    display_names = set()

    while True:
        print(f"🔎 Fetching page {params['page']} ...")

        response = requests.get(url, params=params)
        data = response.json()

        # 결과가 없으면 종료
        if "results" not in data or len(data["results"]) == 0:
            break

        # display_name 추출
        for c in data["results"]:
            name = c.get("display_name")
            if name:
                display_names.add(name)

        # 마지막 페이지면 종료
        if params["page"] >= data["meta"]["page"]:
            break

        params["page"] += 1
        time.sleep(0.5)  # 너무 빠르게 호출하지 않도록 딜레이

    return sorted(display_names)


if __name__ == "__main__":
    concepts = fetch_level2_concepts()

    print("\n=== Level 2 Concepts (Display Names) ===")
    for name in concepts:
        print(name)

    print(f"\n총 개수: {len(concepts)}")
