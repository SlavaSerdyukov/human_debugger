from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_session
from app.main import app


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    local_session = sessionmaker(bind=engine)

    def override_session() -> Generator[Session, None, None]:
        db = local_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_session] = override_session
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_favicon_does_not_404(client: TestClient) -> None:
    response = client.get("/favicon.ico")

    assert response.status_code == 200
    assert "image/svg+xml" in response.headers["content-type"]


def test_seed_demo_supports_browser_get(client: TestClient) -> None:
    response = client.get("/seed-demo", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/debug-report"


def test_seed_demo_supports_dashboard_post(client: TestClient) -> None:
    response = client.post("/seed-demo", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/debug-report"


def test_entry_post_uses_expected_redirect(client: TestClient) -> None:
    response = client.post(
        "/entries",
        data={
            "date": "2026-05-17",
            "text": "Debugged endpoint friction.",
            "mood": "7",
            "energy": "6",
            "focus": "8",
            "stress": "3",
            "sleep_hours": "7.5",
            "tags": "shipping",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/entries"


def test_debug_report_api_exposes_new_observability_sections(client: TestClient) -> None:
    response = client.get("/api/debug-report")

    assert response.status_code == 200
    payload = response.json()
    assert "behavior_loops" in payload
    assert "semantic_memory" in payload
    assert "rolling" in payload["metrics"]
