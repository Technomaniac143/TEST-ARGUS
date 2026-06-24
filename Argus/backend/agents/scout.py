import re

from backend.schemas.search import ParsedQuery


class ScoutAgent:
    """Parses natural-language business research queries."""

    def parse_query(self, query: str) -> ParsedQuery:
        cleaned = re.sub(r"\s+", " ", query.strip())
        if not cleaned:
            return ParsedQuery(category="businesses", location="unknown")

        match = re.match(r"(?P<category>.+?)\s+(?:in|near|around)\s+(?P<location>.+)", cleaned, re.I)
        if match:
            category = self._normalize_category(match.group("category"))
            location = self._normalize_location(match.group("location"))
            return ParsedQuery(category=category, location=location)

        fallback = self._parse_without_preposition(cleaned)
        if fallback:
            return fallback

        return ParsedQuery(category=self._normalize_category(cleaned), location="unknown")

    def _parse_without_preposition(self, cleaned: str) -> ParsedQuery | None:
        known_categories = [
            "roofing contractors",
            "family lawyers",
            "physiotherapists",
            "cardiologists",
            "cardiologist",
            "restaurants",
            "restaurant",
            "electricians",
            "electrician",
            "hospitals",
            "hospital",
            "dentists",
            "dentist",
            "plumbers",
            "plumber",
            "schools",
            "school",
        ]
        lowered = cleaned.lower()
        for category in sorted(known_categories, key=len, reverse=True):
            if lowered.startswith(f"{category} "):
                return ParsedQuery(
                    category=self._normalize_category(category),
                    location=self._normalize_location(cleaned[len(category) :]),
                )
        parts = cleaned.rsplit(" ", 1)
        if len(parts) == 2:
            return ParsedQuery(category=self._normalize_category(parts[0]), location=self._normalize_location(parts[1]))
        return None

    def _normalize_category(self, value: str) -> str:
        category = value.strip().lower()
        singular_map = {
            "cardiologist": "cardiologists",
            "dentist": "dentists",
            "plumber": "plumbers",
            "electrician": "electricians",
            "restaurant": "restaurants",
            "school": "schools",
            "hospital": "hospitals",
            "physiotherapist": "physiotherapists",
            "family lawyer": "family lawyers",
            "roofing contractor": "roofing contractors",
        }
        return singular_map.get(category, category)

    def _normalize_location(self, value: str) -> str:
        location = value.strip().lower().strip(",")
        location = re.sub(r"\s*,\s*", ", ", location)
        aliases = {
            "trichy": "trichy",
            "tiruchirappalli": "trichy",
            "chennai tamil nadu": "chennai",
            "chennai, tamil nadu": "chennai",
            "coimbatore tamil nadu": "coimbatore",
            "coimbatore, tamil nadu": "coimbatore",
            "madurai tamil nadu": "madurai",
            "madurai, tamil nadu": "madurai",
        }
        return aliases.get(location, location)
