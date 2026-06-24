from urllib.parse import parse_qsl, parse_qs, urlencode, unquote, urlparse, urlunparse


class UrlQualityService:
    """Filters URLs that are unlikely to be useful business evidence."""

    blocked_hosts = {
        "accounts.google.com",
        "login.live.com",
        "support.google.com",
    }
    blocked_terms = [
        "/login",
        "/signin",
        "/share",
        "/maps/",
        "/search?",
        "tbm=isch",
        "utm_medium=ad",
        "doubleclick",
        "googleadservices",
        "/news/",
    ]
    tracking_params = {
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_term",
        "utm_content",
        "gclid",
        "fbclid",
        "msclkid",
    }

    def normalize(self, url: str) -> str:
        parsed = urlparse(url)
        if parsed.netloc.endswith("google.com") and parsed.path == "/url":
            query = parse_qs(parsed.query)
            if query.get("q"):
                url = query["q"][0]
                parsed = urlparse(url)
        scheme = (parsed.scheme or "https").lower()
        host = parsed.netloc.lower().removeprefix("www.")
        path = parsed.path.rstrip("/") or "/"
        query_items = [
            (key, value)
            for key, value in parse_qsl(parsed.query, keep_blank_values=True)
            if key.lower() not in self.tracking_params and not key.lower().startswith("utm")
        ]
        query = urlencode(query_items)
        return urlunparse((scheme, host, path, "", query, ""))

    def reject_reason(self, url: str) -> str | None:
        cleaned = unquote(url).lower()
        parsed = urlparse(url)
        host = parsed.netloc.lower().removeprefix("www.")
        if parsed.scheme not in {"http", "https"}:
            return "unsupported scheme"
        if host in self.blocked_hosts:
            return "login or support host"
        if parsed.path.lower().endswith(".pdf"):
            return "pdf document"
        for term in self.blocked_terms:
            if term in cleaned:
                return "irrelevant search, ad, login, map, or share URL"
        return None
