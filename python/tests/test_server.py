from __future__ import annotations

import base64
from pathlib import Path

from fastapi.testclient import TestClient

from gti.client import GenerateImageResult
from gti.server import create_app


class FakeClient:
    def __init__(self, **overrides):
        self.overrides = overrides

    def generate_image(self, *, prompt, model, output_path, dry_run, debug, debug_dir=None):
        if dry_run:
            return GenerateImageResult(
                mode="dry-run",
                warnings=[],
                request={"body": {"model": model, "prompt": prompt}},
            )

        Path(output_path).write_bytes(base64.b64decode("iVBORw0KGgo="))
        return GenerateImageResult(
            mode="live",
            warnings=[],
            response_id="resp_123",
            session_id="session_123",
            saved_path=output_path,
            revised_prompt="revised",
            response={"status": 200},
        )


def test_index_renders(tmp_path):
    app = create_app(client_factory=FakeClient, output_dir=tmp_path)
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "Gpt-imagen v2" in response.text


def test_generate_dry_run(tmp_path):
    app = create_app(client_factory=FakeClient, output_dir=tmp_path)
    client = TestClient(app)

    response = client.post(
        "/api/generate",
        json={"prompt": "flat blue square", "model": "gpt-5.4", "dry_run": True},
    )

    assert response.status_code == 200
    assert response.json()["mode"] == "dry-run"
    assert response.json()["image_url"] is None


def test_generate_live_returns_image_url(tmp_path):
    app = create_app(client_factory=FakeClient, output_dir=tmp_path)
    client = TestClient(app)

    response = client.post("/api/generate", json={"prompt": "flat blue square"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "live"
    assert payload["image_url"].startswith("/api/images/image-")

    image_response = client.get(payload["image_url"])
    assert image_response.status_code == 200
    assert image_response.headers["content-type"] == "image/png"
