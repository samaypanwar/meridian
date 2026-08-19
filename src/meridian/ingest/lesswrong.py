from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

import httpx

GRAPHQL_URL = "https://www.lesswrong.com/graphql"
LW_HOSTS = {
    "www.lesswrong.com",
    "lesswrong.com",
    "www.alignmentforum.org",
    "alignmentforum.org",
}
POST_ID_RE = re.compile(r"/p/([A-Za-z0-9]+)")

POST_QUERY = """
query MeridianFetchPost($id: String!) {
  post(input: { selector: { _id: $id } }) {
    result {
      title
      url
      postedAt
      user { displayName username }
      contents { markdown }
    }
  }
}
"""


def is_lesswrong_url(url: str) -> bool:
    try:
        return urlparse(url).netloc.removeprefix("www.") in {
            h.removeprefix("www.") for h in LW_HOSTS
        }
    except Exception:
        return False


def post_id_from_url(url: str) -> str | None:
    match = POST_ID_RE.search(url)
    return match.group(1) if match else None


def fetch_text(url: str) -> tuple[str, dict[str, Any]]:
    post_id = post_id_from_url(url)
    if post_id is None:
        raise ValueError(f"Could not extract LessWrong post id from {url}")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    response = httpx.post(
        GRAPHQL_URL,
        json={"query": POST_QUERY, "variables": {"id": post_id}},
        headers=headers,
        timeout=60.0,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("errors"):
        raise ValueError(payload["errors"][0].get("message", "LessWrong GraphQL error"))

    result = payload.get("data", {}).get("post", {}).get("result")
    if result is None:
        raise ValueError(f"LessWrong post not found: {post_id}")

    markdown = (result.get("contents") or {}).get("markdown") or ""
    if not markdown.strip():
        raise ValueError("LessWrong post had no extractable body")

    author = None
    user = result.get("user") or {}
    author = user.get("displayName") or user.get("username")

    words = len(markdown.split())
    meta: dict[str, Any] = {
        "title": result.get("title") or url,
        "author": author,
        "words": words,
        "url": url,
        "posted_at": result.get("postedAt"),
        "engine": "lesswrong-graphql",
    }
    return markdown, meta
