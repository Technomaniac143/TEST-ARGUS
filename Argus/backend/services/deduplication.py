from rapidfuzz import fuzz

from backend.schemas.extraction import ExtractedBusiness
from backend.utils.text import normalize_phone, normalize_text, normalize_url


class DeduplicationService:
    """Merges likely duplicate business records while preserving evidence."""

    def deduplicate(self, records: list[ExtractedBusiness]) -> tuple[list[ExtractedBusiness], int]:
        merged: list[ExtractedBusiness] = []
        duplicates_removed = 0

        for record in records:
            match = next((item for item in merged if self._is_duplicate(item, record)), None)
            if match:
                duplicates_removed += 1
                self._merge(match, record)
            else:
                merged.append(record.model_copy(deep=True))

        return merged, duplicates_removed

    def _is_duplicate(self, left: ExtractedBusiness, right: ExtractedBusiness) -> bool:
        if normalize_phone(left.phone) and normalize_phone(left.phone) == normalize_phone(right.phone):
            return True
        if normalize_url(left.website) and normalize_url(left.website) == normalize_url(right.website):
            return True

        name_score = fuzz.token_set_ratio(normalize_text(left.name), normalize_text(right.name))
        address_score = fuzz.token_set_ratio(normalize_text(left.address), normalize_text(right.address))
        if name_score > 90 and (address_score > 85 or not left.address or not right.address):
            return True
        return False

    def _merge(self, target: ExtractedBusiness, incoming: ExtractedBusiness) -> None:
        for field in ["name", "category", "location", "phone", "address", "website", "email", "services", "working_hours"]:
            if getattr(target, field) is None and getattr(incoming, field) is not None:
                setattr(target, field, getattr(incoming, field))
        target.evidence.extend(incoming.evidence)
