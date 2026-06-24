import re
from urllib.parse import urlparse


PHONE_RE = re.compile(r"(?:(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4})")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
HOURS_RE = re.compile(
    r"(?i)\b(?:mon|tue|wed|thu|fri|sat|sun)[a-z]*\b[^.\n]{0,80}(?:am|pm|closed)"
)
RATING_RE = re.compile(r"(?i)\b(?:rating|rated)?\s*([1-5](?:\.\d)?)\s*(?:/ ?5|stars?)\b")
REVIEW_COUNT_RE = re.compile(r"(?i)\b([0-9][0-9,]*)\s+(?:reviews?|ratings?)\b")
SOCIAL_LINK_RE = re.compile(r"https?://(?:www\.)?(?:facebook|linkedin|instagram|x|twitter)\.com/[^\s\"'<>]+", re.I)
IMAGE_URL_RE = re.compile(r"https?://[^\s\"'<>]+\.(?:png|jpe?g|webp|gif)", re.I)


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    value = value.lower().strip()
    value = re.sub(r"[^\w\s]", " ", value)
    value = re.sub(r"\b(?:llc|inc|pllc|clinic|center|centre|company|co|the)\b", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def normalize_phone(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\D", "", value)


def normalize_url(value: str | None) -> str:
    if not value:
        return ""
    parsed = urlparse(value if "://" in value else f"https://{value}")
    host = parsed.netloc.lower().removeprefix("www.")
    return host.rstrip("/")


def first_match(pattern: re.Pattern[str], text: str) -> str | None:
    match = pattern.search(text)
    return match.group(0).strip().strip(".,;:") if match else None


def extract_rating(text: str) -> str | None:
    match = RATING_RE.search(text)
    return match.group(1) if match else None


def extract_review_count(text: str) -> str | None:
    match = REVIEW_COUNT_RE.search(text)
    return match.group(1).replace(",", "") if match else None


def extract_links(pattern: re.Pattern[str], text: str, limit: int = 5) -> str | None:
    matches = []
    for match in pattern.findall(text):
        cleaned = str(match).strip().strip(".,;:")
        if cleaned not in matches:
            matches.append(cleaned)
        if len(matches) >= limit:
            break
    return ", ".join(matches) if matches else None
