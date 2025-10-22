# tools/web_browse.py

# A web-browsing tool that uses Google Programmable Search (if GOOGLE_API_KEY and GOOGLE_CSE_ID are set) or falls back to Bing when available.
# Environment variables:
# - GOOGLE_API_KEY: API key for Google Programmable Search JSON API
# - GOOGLE_CSE_ID: Search Engine ID (cx) for Programmable Search
# - BING_API_KEY: fallback Bing API key
# - OPENAI_API_KEY or ANTHROPIC_API_KEY: LLM summarization credentials

import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import urllib.robotparser
from typing import List, Dict

# Optional LLM clients
try:
    import openai
except Exception:
    openai = None

try:
    import anthropic
except Exception:
    anthropic = None

USER_AGENT = "claude-chatbot-detdei/1.0 (+https://github.com/yakiniku35/claude-chatbot-detdei)"
BING_ENDPOINT = "https://api.bing.microsoft.com/v7.0/search"
GOOGLE_SEARCH_ENDPOINT = "https://www.googleapis.com/customsearch/v1"

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.environ.get("GOOGLE_CSE_ID")
BING_API_KEY = os.environ.get("BING_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

def allowed_by_robots(url: str, user_agent: str = "*") -> bool:
    try:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(user_agent, url)
    except Exception:
        return True

def google_search(query: str, top_k: int = 3) -> List[Dict]:
    """Search using Google Programmable Search JSON API. Requires GOOGLE_API_KEY and GOOGLE_CSE_ID."""
    if not (GOOGLE_API_KEY and GOOGLE_CSE_ID):
        raise RuntimeError("GOOGLE_API_KEY and GOOGLE_CSE_ID must be set to use Google search")
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CSE_ID,
        "q": query,
        "num": min(top_k, 10),
    }
    headers = {"User-Agent": USER_AGENT}
    r = requests.get(GOOGLE_SEARCH_ENDPOINT, params=params, headers=headers, timeout=10)
    r.raise_for_status()
    data = r.json()
    results = []
    for item in data.get("items", [])[:top_k]:
        results.append({
            "title": item.get("title"),
            "url": item.get("link"),
            "snippet": item.get("snippet", "")
        })
    return results

def bing_search(query: str, top_k: int = 3) -> List[Dict]:
    if not BING_API_KEY:
        raise RuntimeError("BING_API_KEY missing in environment")
    headers = {"Ocp-Apim-Subscription-Key": BING_API_KEY, "User-Agent": USER_AGENT}
    params = {"q": query, "count": top_k}
    r = requests.get(BING_ENDPOINT, headers=headers, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    results = []
    for item in data.get("webPages", {}).get("value", []):
        results.append({"title": item.get("name"), "url": item.get("url"), "snippet": item.get("snippet", "")})
    return results

def fetch_page_text(url: str, timeout: int = 10) -> str:
    if not allowed_by_robots(url):
        raise RuntimeError(f"Fetching disallowed by robots.txt: {url}")
    headers = {"User-Agent": USER_AGENT}
    r = requests.get(url, headers=headers, timeout=timeout)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    for s in soup(["script", "style", "noscript", "iframe"]):
        s.decompose()
    article = soup.find("article")
    main = soup.find("main")
    container = article or main or soup
    paragraphs = [p.get_text(separator=" ", strip=True) for p in container.find_all("p")]
    if not paragraphs:
        meta = soup.find("meta", attrs={"name":"description"}) or soup.find("meta", attrs={"property":"og:description"})
        if meta and meta.get("content"):
            paragraphs = [meta["content"]]
    text = "\n\n".join(paragraphs)
    MAX_CHARS = 150_000
    return text[:MAX_CHARS]

def chunk_text(text: str, max_chars: int = 16000) -> List[str]:
    if len(text) <= max_chars:
        return [text]
    parts = text.split("\n\n")
    chunks = []
    cur = ""
    for p in parts:
        if len(cur) + len(p) + 2 <= max_chars:
            cur = cur + ("\n\n" if cur else "") + p
        else:
            if cur:
                chunks.append(cur)
            if len(p) > max_chars:
                for i in range(0, len(p), max_chars):
                    chunks.append(p[i:i+max_chars])
                cur = ""
            else:
                cur = p
    if cur:
        chunks.append(cur)
    return chunks

def summarize_with_llm(page_text: str, question: str, max_tokens: int = 400) -> str:
    if OPENAI_API_KEY and openai:
        openai.api_key = OPENAI_API_KEY
        prompt = (
            "You are a helpful assistant. Use the page text below to answer the question.\n\n"
            "Page text:\n"
            f"{page_text}\n\n"
            "Question:\n"
            f"{question}\n\n"
            "Provide a short answer (2-6 sentences). At the end, include a short quoted snippet (<=40 chars) that supports the answer."
        )
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini" if hasattr(openai, "__version__") else "gpt-4o-mini",
            messages=[{"role":"user", "content":prompt}],
            max_tokens=max_tokens,
            temperature=0.2,
        )
        return resp["choices"][0]["message"]["content"].strip()
    elif ANTHROPIC_API_KEY and anthropic:
        client = anthropic.Client(ANTHROPIC_API_KEY)
        prompt = (f"{anthropic.HUMAN_PROMPT}{question}\n\nUse the following page text to answer:\n\n{page_text}\n\n{anthropic.AI_PROMPT}")
        resp = client.completions.create(model="claude-2.1", prompt=prompt, max_tokens_to_sample=max_tokens, temperature=0.0)
        return resp.completion.strip()
    else:
        raise RuntimeError("No LLM credentials found. Set OPENAI_API_KEY or ANTHROPIC_API_KEY and install the client library.")

def browse_and_answer(question: str, top_k: int = 3, provider: str = "auto", synthesize: bool = True) -> Dict:
    """provider: "google", "bing", or "auto" (prefer Google if keys present)
    """
    search_results = []
    if provider == "google" or (provider == "auto" and GOOGLE_API_KEY and GOOGLE_CSE_ID):
        search_results = google_search(question, top_k=top_k)
    elif provider == "bing" or (provider == "auto" and BING_API_KEY and not (GOOGLE_API_KEY and GOOGLE_CSE_ID)):
        search_results = bing_search(question, top_k=top_k)
    else:
        # fallback order: Google -> Bing
        if GOOGLE_API_KEY and GOOGLE_CSE_ID:
            search_results = google_search(question, top_k=top_k)
        elif BING_API_KEY:
            search_results = bing_search(question, top_k=top_k)
        else:
            raise RuntimeError("No search provider configured. Set GOOGLE_API_KEY and GOOGLE_CSE_ID or BING_API_KEY.")

    answers = []
    for r in search_results:
        url = r.get("url")
        try:
            page_text = fetch_page_text(url)
        except Exception as e:
            answers.append({**r, "summary": f"Could not fetch page: {e}"})
            continue
        chunks = chunk_text(page_text, max_chars=12000)
        chunk_summaries = []
        for c in chunks:
            try:
                s = summarize_with_llm(c, question)
                chunk_summaries.append(s)
            except Exception as e:
                chunk_summaries.append(f"[summarization failed: {e}]")
        combined = "\n\n".join(chunk_summaries)
        answers.append({**r, "summary": combined})

    final_answer = None
    if synthesize:
        synth_prompt = "You are a synthesizer. Given these summarized search results, write a concise (2-5 sentence) answer to the original question and list 1-2 source URLs as citations.\n\n"
        synth_prompt += f"Question: {question}\n\nSummaries:\n"
        for i, a in enumerate(answers, start=1):
            synth_prompt += f"[{i}] {a.get('title')} - {a.get('url')}\n{a.get('summary')}\n\n"
        try:
            final_answer = summarize_with_llm(synth_prompt, question)
        except Exception:
            final_answer = None
    return {"question": question, "results": answers, "final_answer": final_answer}

if __name__ == "__main__":
    q = "What's the latest Python release?"
    try:
        out = browse_and_answer(q, top_k=2)
        print("FINAL ANSWER:\n", out["final_answer"])
        for r in out["results"]:
            print(f"\n== {r.get('title')} ==\n{r.get('url')}\nSummary:\n{r.get('summary')[:1000]}\n")
    except Exception as e:
        print("Error:", e)