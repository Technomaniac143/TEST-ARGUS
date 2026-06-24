from collections import defaultdict

from backend.schemas.extraction import ExtractedBusiness, FieldEvidence
from backend.utils.text import normalize_phone, normalize_text, normalize_url


class ConflictCandidate:
    def __init__(self, field: str, value1: str, value2: str, source1: str, source2: str):
        self.field = field
        self.value1 = value1
        self.value2 = value2
        self.source1 = source1
        self.source2 = source2


class ConflictDetectionService:
    """Finds contradictory evidence for the same field."""

    comparable_fields = {"phone", "address", "website", "email"}

    def detect(self, business: ExtractedBusiness) -> list[ConflictCandidate]:
        by_field: dict[str, list[FieldEvidence]] = defaultdict(list)
        for item in business.evidence:
            if item.field in self.comparable_fields:
                by_field[item.field].append(item)

        conflicts: list[ConflictCandidate] = []
        for field, items in by_field.items():
            seen: dict[str, FieldEvidence] = {}
            for item in items:
                key = self._normalize(field, item.value)
                if not key:
                    continue
                for existing_key, existing in seen.items():
                    if existing_key != key:
                        conflicts.append(
                            ConflictCandidate(field, existing.value, item.value, existing.source, item.source)
                        )
                        break
                seen.setdefault(key, item)
        return conflicts

    def _normalize(self, field: str, value: str) -> str:
        if field == "phone":
            return normalize_phone(value)
        if field == "website":
            return normalize_url(value)
        return normalize_text(value)
