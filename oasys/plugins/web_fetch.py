"""OASYS plugin: fetch a URL and return readable text (Markdown-ish)."""
import re
import requests
from pathlib import Path

NAME = "web_fetch"
DESCRIPTION = "Fetch a web page and return its text. Usage: /run web_fetch <url> [max_chars]"


def _strip_html(html: str) -> str:
    # remove scripts/styles
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    # keep some structure
    html = re.sub(r"<(h[1-6])[^>]*>", r"\n\n## ", html, flags=re.I)
    html = re.sub(r"<(li|p|br|div)[^>]*>", "\n", html, flags=re.I)
    text = re.sub(r"<[^>]+>", "", html)
    text = re.sub(r"&[a-z]+;", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def run(args: str, ctx: dict) -> str:
    parts = args.split()
    if not parts:
        return "[web_fetch] usage: web_fetch <url> [max_chars]"
    url = parts[0]
    cap = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 6000
    try:
        r = requests.get(url, timeout=20, headers={"User-Agent": "OASYS/1.0"})
        r.raise_for_status()
        text = _strip_html(r.text)
        return f"[web_fetch] {url} ({len(text)} chars)\n\n" + text[:cap]
    except Exception as e:
        return f"[web_fetch] error: {e}"
