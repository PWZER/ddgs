"""Sogou search engine implementation."""

from __future__ import annotations

from typing import Any, ClassVar

from ..base import BaseSearchEngine
from ..results import TextResult


class Sogou(BaseSearchEngine[TextResult]):
    """Sogou search engine."""

    name = "sogou"
    category = "text"
    provider = "sogou"
    disabled = False

    search_url = "https://www.sogou.com/web"
    search_method = "GET"

    items_xpath = '//div[contains(@class, "vrwrap")]'
    elements_xpath: ClassVar[dict[str, str]] = {
        "title": './/h3[contains(@class, "vr-title")]/a//text()',
        "href": './/h3[contains(@class, "vr-title")]/a/@href',
        "body": (
            './/div[contains(@class, "text-layout")]//p[contains(@class, "star-wiki")]//text() | '
            './/div[contains(@class, "fz-mid space-txt")]//text()'
        ),
    }

    time_range_dict: ClassVar[dict[str, str]] = {
        "d": "inttime_day",
        "w": "inttime_week",
        "m": "inttime_month",
        "y": "inttime_year",
    }

    def build_payload(
        self, query: str, region: str, safesearch: str, timelimit: str | None, page: int = 1, **kwargs: Any
    ) -> dict[str, Any]:
        """Build a payload for the Sogou search request."""
        payload = {
            "query": query,
            "page": page,
        }

        # Add time range filter if specified
        if timelimit and timelimit in self.time_range_dict:
            payload["s_from"] = self.time_range_dict[timelimit]
            payload["tsn"] = 1

        return payload

    def post_extract_results(self, results: list[TextResult]) -> list[TextResult]:
        """Post-process search results to handle Sogou's URL redirects."""
        base_url = "https://www.sogou.com"
        post_results = []

        for result in results:
            # Handle Sogou's redirect URLs
            if result.href.startswith("/link?url="):
                result.href = f"{base_url}{result.href}"

            # Only add results with both title and URL
            if result.title and result.href:
                post_results.append(result)

        return post_results
