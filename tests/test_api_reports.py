"""Integration tests for reports API endpoints."""

from fastapi.testclient import TestClient

from backend.core.app import create_app
from backend.core.models import Evidence, Source


def test_api_generate_and_retrieve_report() -> None:
    app = create_app()
    client = TestClient(app)

    src = Source(
        title="Attention Is All You Need", authors=["Vaswani, A."], publication_date="2017"
    )
    ev = Evidence(
        source_id=src.id,
        content="The Transformer model architecture eschews recurrence and relies entirely on self-attention mechanisms.",
        section="1. Introduction",
        page_number=2,
    )

    payload = {
        "question": "How do attention mechanisms replace recurrence?",
        "discipline": "Computer Science",
        "verified_evidence": [ev.model_dump(mode="json")],
        "sources": [src.model_dump(mode="json")],
    }

    # 1. Generate report
    resp = client.post("/api/v1/reports/generate", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    report_id = data["report_id"]
    assert "report_markdown" in data
    assert data["validation"]["is_valid"] is True

    # 2. Retrieve report
    resp_get = client.get(f"/api/v1/reports/{report_id}")
    assert resp_get.status_code == 200
    assert resp_get.json()["report_id"] == report_id

    # 3. Retrieve claims
    resp_claims = client.get(f"/api/v1/reports/{report_id}/claims")
    assert resp_claims.status_code == 200
    assert len(resp_claims.json()) >= 1

    # 4. Retrieve validation
    resp_val = client.get(f"/api/v1/reports/{report_id}/validation")
    assert resp_val.status_code == 200
    assert resp_val.json()["is_valid"] is True

    # 5. List artifacts
    resp_art = client.get(f"/api/v1/reports/{report_id}/artifacts")
    assert resp_art.status_code == 200
    artifacts = resp_art.json()
    assert any(a["filename"] == "report.md" for a in artifacts)

    # 6. Download artifact
    resp_dl = client.get(f"/api/v1/reports/{report_id}/artifacts/report.md")
    assert resp_dl.status_code == 200
    assert "# Empirical Investigation into" in resp_dl.text

    # 7. Path traversal defense check
    resp_bad = client.get(f"/api/v1/reports/{report_id}/artifacts/..%2f..%2fetc%2fpasswd")
    assert resp_bad.status_code in [403, 404]

    # 8. Not found check
    resp_404 = client.get("/api/v1/reports/00000000-0000-0000-0000-000000000000")
    assert resp_404.status_code == 404
