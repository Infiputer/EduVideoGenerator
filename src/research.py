import os
import requests
from dotenv import load_dotenv

load_dotenv()

EXA_API_KEY = os.getenv("EXA_API_KEY", "")


def search(topic: str, num_results: int = 10) -> list[dict]:
    """Search for educational content on a topic using Exa AI."""
    if not EXA_API_KEY:
        print("Warning: EXA_API_KEY not set, using mock data")
        return [
            {
                "title": f"Overview of {topic}",
                "url": "",
                "text": f"Educational content about {topic}.",
            }
            for _ in range(3)
        ]

    headers = {
        "Authorization": f"Bearer {EXA_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    data = {
        "query": f"educational tutorial about {topic}",
        "num_results": num_results,
        "type": "auto",
    }

    try:
        response = requests.post(
            "https://api.exa.ai/search", headers=headers, json=data, timeout=30
        )
        response.raise_for_status()
        results = response.json().get("results", [])
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "text": r.get("text", "")[:2000],
            }
            for r in results
        ]
    except Exception as e:
        print(f"Exa search failed: {e}")
        return [
            {
                "title": f"Overview of {topic}",
                "url": "",
                "text": f"Educational content about {topic}.",
            }
            for _ in range(3)
        ]


def get_content(url: str) -> str:
    """Get content from a URL using Exa's contents endpoint."""
    if not EXA_API_KEY:
        return ""

    headers = {
        "Authorization": f"Bearer {EXA_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    data = {"urls": [url]}

    try:
        response = requests.post(
            "https://api.exa.ai/contents", headers=headers, json=data, timeout=30
        )
        response.raise_for_status()
        results = response.json().get("results", [])
        if results:
            return results[0].get("text", "")[:5000]
    except Exception as e:
        print(f"Exa contents failed: {e}")

    return ""
