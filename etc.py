import requests

AUTHOR_ID = "A5060719444"

# 저자의 모든 논문 가져오기
url = f"https://api.openalex.org/works?filter=author.id:{AUTHOR_ID}&per-page=200"
response = requests.get(url)
data = response.json()

topics = {}

for work in data.get("results", []):
    concepts = work.get("concepts", [])
    for c in concepts:
        name = c["display_name"]
        score = c["score"]
        topics[name] = topics.get(name, 0) + score   # score 누적

# 점수 기준 정렬
sorted_topics = sorted(topics.items(), key=lambda x: -x[1])

print("=== Kilian Batzner Topics ===")
for name, score in sorted_topics:
    print(f"{name}  (score={round(score, 4)})")
