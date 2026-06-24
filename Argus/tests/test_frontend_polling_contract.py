from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_frontend_polling_uses_basic_endpoint() -> None:
    api = (ROOT / "frontend" / "lib" / "api.ts").read_text(encoding="utf-8")
    dashboard = (ROOT / "frontend" / "components" / "ResearchDashboard.tsx").read_text(encoding="utf-8")

    assert "getBasicResearch" in api
    assert "/api/research/${sessionId}/basic" in api
    assert "getBasicResearch(sessionId)" in dashboard
    assert "getResearch(sessionId)" not in dashboard


def test_frontend_polling_has_stop_conditions() -> None:
    dashboard = (ROOT / "frontend" / "components" / "ResearchDashboard.tsx").read_text(encoding="utf-8")

    assert 'latest.status === "complete"' in dashboard
    assert 'latest.status === "failed"' in dashboard
    assert 'latest.status === "partial" && latest.report_ready' in dashboard
    assert "pollingFailureCountRef.current >= 2" in dashboard
