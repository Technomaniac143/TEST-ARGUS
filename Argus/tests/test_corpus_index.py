from backend.offline_corpus.corpus import classify_support, corpus_index, search_offline
from backend.schemas.search import ParsedQuery


def test_corpus_index_classifies_full_partial_and_unsupported_queries() -> None:
    assert classify_support(ParsedQuery(category="cardiologists", location="birmingham")) == "FULL_CORPUS_MATCH"
    assert classify_support(ParsedQuery(category="dentists", location="dallas")) == "PARTIAL_CATEGORY_MATCH"
    assert classify_support(ParsedQuery(category="plumbers", location="birmingham")) == "PARTIAL_LOCATION_MATCH"
    assert classify_support(ParsedQuery(category="restaurants", location="tokyo")) == "UNSUPPORTED_OFFLINE_QUERY"


def test_unsupported_offline_query_returns_no_business_results() -> None:
    parsed = ParsedQuery(category="restaurants", location="tokyo")

    assert search_offline(parsed, limit=100) == []

    index = corpus_index(parsed)
    assert index["support_level"] == "UNSUPPORTED_OFFLINE_QUERY"
    assert "Cardiologists in Birmingham" in index["suggested_queries"]


def test_partial_query_suggests_matching_supported_pair() -> None:
    category_partial = corpus_index(ParsedQuery(category="dentists", location="dallas"))
    location_partial = corpus_index(ParsedQuery(category="plumbers", location="birmingham"))

    assert category_partial["suggested_queries"] == ["Dentists in Austin"]
    assert location_partial["suggested_queries"] == ["Cardiologists in Birmingham"]
