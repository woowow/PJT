import requests
import xml.etree.ElementTree as ET

def search_arxiv(query, max_results=20):
    url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    }

    response = requests.get(url, params=params)
    root = ET.fromstring(response.text)

    ns = {'atom': 'http://www.w3.org/2005/Atom'}

    papers = []

    for entry in root.findall('atom:entry', ns):
        papers.append({
            'title': entry.find('atom:title', ns).text.strip(),
            'summary': entry.find('atom:summary', ns).text.strip(),
            'published': entry.find('atom:published', ns).text,
            'updated': entry.find('atom:updated', ns).text,
            'arxiv_id': entry.find('atom:id', ns).text.split('/abs/')[-1],
            'pdf_url': entry.find('atom:link[@type="application/pdf"]', ns).attrib['href'],
            'authors': [a.find('atom:name', ns).text for a in entry.findall('atom:author', ns)],
            'categories': entry.find('atom:category', ns).attrib['term']
        })
    return papers
