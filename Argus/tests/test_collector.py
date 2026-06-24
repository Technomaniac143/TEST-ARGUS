import pytest

from backend.agents.scout import ScoutAgent
from backend.schemas.search import SearchResult
from backend.services.collector import CollectorService


class FakeResponse:
    text = """
    <html>
      <head><title>Birmingham Heart Specialists - Home</title></head>
      <body>
        Phone 205-555-0184.
        Email referrals@birminghamheart.example.
        Visit 2010 Brookwood Medical Center Dr, Birmingham, AL.
        Hours Mon-Fri 8am-5pm.
        Services echocardiography and vascular screening.
      </body>
    </html>
    """

    def raise_for_status(self) -> None:
        return None


class FakeAsyncClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def get(self, *args, **kwargs):
        return FakeResponse()


@pytest.mark.anyio
async def test_collector_extracts_business_fields(monkeypatch) -> None:
    monkeypatch.setattr("backend.services.collector.httpx.AsyncClient", FakeAsyncClient)
    parsed = ScoutAgent().parse_query("Cardiologists in Birmingham")
    result = SearchResult(
        title="Birmingham Heart Specialists",
        url="https://birminghamheart.example",
        snippet="Cardiology clinic",
        source="Mock",
    )

    business = await CollectorService().collect_one(result, parsed)

    assert business.name == "Birmingham Heart Specialists"
    assert business.phone == "205-555-0184"
    assert business.email == "referrals@birminghamheart.example"
    assert business.address is not None
    assert len(business.evidence) >= 5
