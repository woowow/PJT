import requests

SEMANTIC_SCHOLAR_API_KEY = "YOUR_API_KEY"

def fetch_semantic_scholar(arxiv_id):
    url = f"https://api.semanticscholar.org/graph/v1/paper/ARXIV:{arxiv_id}"

    fields = "title,citationCount,influentialCitationCount,recentInfluenceScore"

    headers = {"x-api-key": SEMANTIC_SCHOLAR_API_KEY}

    params = {"fields": fields}

    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        return None

    return response.json()
