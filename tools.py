"""Web search and article text extraction. No API key required."""

import ipaddress
import json
import socket
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from ddgs import DDGS
from trafilatura import extract

MAX_RESULTS = 5
MAX_PAGE_BYTES = 2_000_000
MAX_PAGE_CHARS = 12_000


def search_web(query):
    try:
        results = DDGS(timeout=15).text(query, backend="duckduckgo", max_results=MAX_RESULTS)
        return [{"title": item.get("title", ""), "url": item["href"],
                 "snippet": item.get("body", "")[:1000]} for item in results[:MAX_RESULTS]]
    except Exception as exc:
        raise RuntimeError(f"Web search failed: {exc}") from exc


def check_public_url(url):
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username:
        raise ValueError("Only public HTTP(S) page URLs are supported.")
    addresses = socket.getaddrinfo(parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
    if any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
        raise ValueError("Local and private network addresses are not supported.")


class PublicRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        check_public_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_page(url):
    try:
        check_public_url(url)
        request = Request(url, headers={"User-Agent": "WebResearchAgent/0.1", "Accept": "text/html,text/plain"})
        with build_opener(PublicRedirects()).open(request, timeout=20) as response:
            content_type = response.headers.get_content_type()
            if content_type not in ("text/html", "application/xhtml+xml", "text/plain"):
                raise ValueError(f"Unsupported page type: {content_type}; use an HTML page.")
            raw = response.read(MAX_PAGE_BYTES + 1)
            if len(raw) > MAX_PAGE_BYTES:
                raise ValueError("Page exceeds the 2 MB download limit.")
            final_url = response.geturl()
            if content_type == "text/plain":
                page = {"text": raw.decode(response.headers.get_content_charset() or "utf-8", errors="replace")}
            else:
                document = extract(raw, url=final_url, output_format="json", with_metadata=True, include_comments=False)
                page = json.loads(document) if document else {}
        content = (page.get("text") or "").strip()
        if not content:
            raise ValueError("No readable article text found; try another page.")
        return {"url": final_url, "title": page.get("title") or final_url,
                "content": content[:MAX_PAGE_CHARS], "truncated": len(content) > MAX_PAGE_CHARS}
    except Exception as exc:
        raise RuntimeError(f"Page fetch failed: {exc}") from exc
