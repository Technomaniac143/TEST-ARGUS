from backend.services.source_reliability import source_reliability


def test_source_reliability_scores_known_sources() -> None:
    official = source_reliability("Official Website")
    facebook = source_reliability("Facebook")

    assert official["source_type"] == "official"
    assert official["reliability_score"] == 95
    assert official["reliability_label"] == "HIGH"
    assert facebook["reliability_score"] < official["reliability_score"]
