SOURCE_RELIABILITY = {
    "Official Website": ("official", 95, "HIGH"),
    "Government License Registry": ("registry", 95, "HIGH"),
    "Professional Directory": ("directory", 90, "HIGH"),
    "Google Business Profile": ("profile", 88, "HIGH"),
    "LinkedIn": ("social_professional", 85, "HIGH"),
    "Industry Association": ("association", 84, "HIGH"),
    "Yelp": ("review_directory", 75, "MEDIUM"),
    "Yellow Pages": ("directory", 72, "MEDIUM"),
    "Facebook": ("social", 65, "MEDIUM_LOW"),
}


def source_reliability(
    source: str,
    agreement_count: int = 1,
    agreement_total: int = 1,
    field_completeness: int = 0,
    has_conflict: bool = False,
) -> dict[str, int | str]:
    source_type, score, label = SOURCE_RELIABILITY.get(source, ("unknown", 50, "LOW"))
    if agreement_total and agreement_count == agreement_total and agreement_total > 1:
        score += 3
    if field_completeness >= 5:
        score += 2
    if has_conflict:
        score -= 8
    score = max(0, min(100, score))
    if score >= 84:
        label = "HIGH"
    elif score >= 70:
        label = "MEDIUM"
    elif score >= 60:
        label = "MEDIUM_LOW"
    else:
        label = "LOW"
    return {
        "source_type": source_type,
        "reliability_score": score,
        "reliability_label": label,
    }
