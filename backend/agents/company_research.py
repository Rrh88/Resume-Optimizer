import os

import requests
from dotenv import load_dotenv

from backend.agents.base import run_agent

load_dotenv()

SYSTEM = (
    "You are a Company Research and Optimization agent. Using the web research provided, "
    "identify the company's culture, values and what it looks for in candidates. "
    "Adjust the language, keywords and emphasis of the resume (summary, bullets, skills order) "
    "to align with them, truthfully. "
    "In reasoning, list 3-4 key values or hiring patterns found and how you applied each."
)


def _search(query, n=4):
    key = os.getenv("TAVILY_API_KEY")
    if not key:
        return []
    try:
        r = requests.post(
            "https://api.tavily.com/search",
            headers={"Authorization": "Bearer " + key},
            json={"query": query, "search_depth": "basic", "max_results": n},
            timeout=30,
        )
        r.raise_for_status()
        return r.json().get("results", [])
    except Exception:
        return []


def research(company, role=""):
    queries = [
        company + " company culture and core values",
        company + " hiring process and what they look for in candidates"
        + ((" for " + role) if role else ""),
    ]
    seen, items = set(), []
    for q in queries:
        for x in _search(q):
            if x["url"] not in seen:
                seen.add(x["url"])
                items.append(x)
    return items


def run(resume, company, role=""):
    items = research(company, role)
    if items:
        ctx = "\n\n".join(
            "SOURCE: " + x["url"] + "\n" + x.get("content", "")[:700] for x in items
        )
    else:
        ctx = (
            "No web results available. Use only widely known public facts "
            "and say in reasoning that web research was unavailable."
        )
    task = (
        "Target company: " + company + "\nTarget role: " + (role or "N/A") + "\n"
        "WEB RESEARCH:\n" + ctx
    )
    r = run_agent(SYSTEM, task, resume)
    if items:
        r.reasoning += "\nSources: " + ", ".join(x["url"] for x in items[:4])
    return r