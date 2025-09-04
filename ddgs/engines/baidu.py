"""Baidu search engine implementation."""

from __future__ import annotations

import json
import logging
import time
from typing import Any, ClassVar

from ..base import BaseSearchEngine
from ..results import TextResult

logger = logging.getLogger(__name__)


class Baidu(BaseSearchEngine[TextResult]):
    """Baidu search engine."""

    name = "baidu"
    category = "text"
    provider = "baidu"
    disabled = False

    search_url = "https://www.baidu.com/s"
    search_method = "GET"

    # Baidu uses JSON response, but we need XPath for ddgs framework
    # We'll override extract_results to handle JSON parsing
    items_xpath = "//dummy"  # Placeholder since we override extract_results
    elements_xpath: ClassVar[dict[str, str]] = {}  # Placeholder since we override extract_results

    time_range_dict: ClassVar[dict[str, int]] = {"d": 86400, "w": 604800, "m": 2592000, "y": 31536000}

    def build_payload(
        self, query: str, region: str, safesearch: str, timelimit: str | None, page: int = 1, **kwargs: Any
    ) -> dict[str, Any]:
        """Build a payload for the Baidu search request."""
        results_per_page = 10
        payload = {
            "wd": query,
            "rn": str(results_per_page),
            "pn": str((page - 1) * results_per_page),
            "tn": "json",
        }

        # Add time range filter if specified
        if timelimit and timelimit in self.time_range_dict:
            now = int(time.time())
            past = now - self.time_range_dict[timelimit]
            payload["gpc"] = f"stf={past},{now}|stftype=1"

        return payload

    def extract_results(self, html_text: str) -> list[TextResult]:
        """Extract search results from Baidu JSON response."""
        try:
            data = json.loads(html_text, strict=False)
        except json.JSONDecodeError:
            return []

        results = []
        if not data.get("feed", {}).get("entry"):
            return results

        for entry in data["feed"]["entry"]:
            if not entry.get("title") or not entry.get("url"):
                continue

            result = TextResult()
            result.title = entry["title"]
            result.href = entry["url"]
            result.body = entry.get("abs", "")

            results.append(result)

        return results

    def request(self, *args: Any, **kwargs: Any) -> str | None:
        """Make a request to the Baidu search engine with CAPTCHA detection."""
        resp = self.http_client.request(*args, **kwargs)

        # Detect Baidu CAPTCHA redirect
        if resp.status_code in (301, 302, 303, 307, 308):
            location = resp.headers.get("Location", "")
            if "wappass.baidu.com/static/captcha" in location:
                return None  # CAPTCHA detected, return None to indicate failure

        if resp.status_code == 200:
            return resp.text
        return None
