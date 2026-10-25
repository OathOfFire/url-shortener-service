import pytest
from fastapi.testclient import TestClient

from app.main import app, urls

client = TestClient(app) # fake request straight to app, nothing online

#Cleanup Fixture
@pytest.fixture(autouse=True)
def clear_urls():
    urls.clear()
    yield
    urls.clear()


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_shorten_returns_code():
    r = client.post("/shorten", json={"url": "https://example.com"})
    assert r.status_code == 201
    assert len(r.json()["code"]) == 6


def test_shorten_rejects_invalid_url():
    r = client.post("/shorten", json={"url": "not a url"})
    assert r.status_code == 422


def test_redirect_goes_to_original():
    code = client.post("/shorten", json={"url": "https://example.com"}).json()["code"]
    r = client.get(f"/{code}", follow_redirects=False)
    assert r.status_code in (302, 307)
    assert r.headers["location"] == "https://example.com/"


def test_redirect_unknown_code_404():
    assert client.get("/nope123").status_code == 404


def test_list_urls():
    client.post("/shorten", json={"url": "https://example.com"})
    assert len(client.get("/urls").json()) == 1


def test_delete_removes_url():
    code = client.post("/shorten", json={"url": "https://example.com"}).json()["code"]
    assert client.delete(f"/{code}").status_code == 204
    assert client.get(f"/{code}", follow_redirects=False).status_code == 404