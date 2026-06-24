from backend.agents.scout import ScoutAgent


def test_parse_category_and_location() -> None:
    parsed = ScoutAgent().parse_query("Cardiologists in Birmingham")

    assert parsed.category == "cardiologists"
    assert parsed.location == "birmingham"


def test_parse_near_query() -> None:
    parsed = ScoutAgent().parse_query("dentists near Atlanta")

    assert parsed.category == "dentists"
    assert parsed.location == "atlanta"


def test_parse_global_query_without_connector() -> None:
    parsed = ScoutAgent().parse_query("Restaurants Tokyo")

    assert parsed.category == "restaurants"
    assert parsed.location == "tokyo"


def test_parse_location_with_comma_and_singular_category() -> None:
    parsed = ScoutAgent().parse_query("Cardiologist in Chennai, Tamil Nadu")

    assert parsed.category == "cardiologists"
    assert parsed.location == "chennai"
