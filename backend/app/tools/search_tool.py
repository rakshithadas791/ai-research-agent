"""
search_tool.py — web_search with an honest, three-source fallback chain.

  1. DuckDuckGo HTML results page — richest results, but its bot-detection
     can block automated/scripted requests.
  2. DuckDuckGo Instant Answer JSON API — official, key-less, but designed
     for short factual lookups ("capital of France"), not open research
     questions, so it legitimately has nothing for most queries.
  3. Wikipedia's search API — official, key-less, generous rate limits,
     and actually has real content for most general research topics.

Each helper returns ("ok", text) | ("no_data", None) | ("unreachable", reason)
so the final message is honest about WHY a source didn't help — "reachable
but had nothing for this query" is a different, more useful signal than
"couldn't connect," and conflating them was misleading in the last version.
"""
import html
import re
import requests


def web_search(query: str, max_results: int = 5) -> str:
    for source_fn in (_duckduckgo_html, _duckduckgo_instant_answer, _wikipedia_search):
        status, payload = source_fn(query, max_results)
        if status == "ok":
            return payload

    return (
        f"No results found for '{query}' across the available free search sources "
        f"(DuckDuckGo HTML, DuckDuckGo Instant Answer, Wikipedia). This can mean the "
        f"query is too narrow/current for these sources, or a source is being rate-"
        f"limited — try rephrasing, or configure a different provider in search_tool.py."
    )


def _duckduckgo_html(query: str, max_results: int):
    try:
        resp = requests.post(
            "https://html.duckduckgo.com/html/",
            data={"q": query},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        resp.raise_for_status()
    except Exception as e:
        return "unreachable", str(e)

    titles = re.findall(r'class="result__a"[^>]*>(.*?)</a>', resp.text)
    snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', resp.text)
    clean = lambda s: html.unescape(re.sub("<.*?>", "", s)).strip()

    results = []
    for i, (t, s) in enumerate(zip(titles, snippets)):
        if i >= max_results:
            break
        results.append(f"{i+1}. {clean(t)} — {clean(s)}")

    if results:
        return "ok", "\n".join(results)
    return "no_data", None


def _duckduckgo_instant_answer(query: str, max_results: int):
    try:
        resp = requests.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return "unreachable", str(e)

    lines = []
    if data.get("AbstractText"):
        source = data.get("AbstractSource", "DuckDuckGo")
        lines.append(f"1. {source}: {data['AbstractText']}")
    for topic in data.get("RelatedTopics", [])[:max_results - 1]:
        text = topic.get("Text") if isinstance(topic, dict) else None
        if text:
            lines.append(f"{len(lines) + 1}. {text}")

    if lines:
        return "ok", "\n".join(lines)
    return "no_data", None


def _wikipedia_search(query: str, max_results: int):
    """Wikipedia's official search API — free, no key, generous rate limits,
    and has real content for most general research topics."""
    try:
        resp = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query", "list": "search", "format": "json",
                "srsearch": query, "srlimit": max_results,
            },
            headers={"User-Agent": "ai-research-agent/1.0"},
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json().get("query", {}).get("search", [])
    except Exception as e:
        return "unreachable", str(e)

    if not results:
        return "no_data", None

    clean = lambda s: html.unescape(re.sub("<.*?>", "", s)).strip()
    lines = [
        f"{i+1}. {r['title']} (Wikipedia) — {clean(r.get('snippet', ''))}"
        for i, r in enumerate(results)
    ]
    return "ok", "\n".join(lines)