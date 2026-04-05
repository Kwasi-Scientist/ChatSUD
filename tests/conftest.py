from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from chat_sud.api import create_app
from chat_sud.config import Settings


@pytest.fixture()
def sample_documents() -> list[dict[str, str]]:
    return json.loads(Path("tests/fixtures/sample_documents.json").read_text(encoding="utf-8"))


@pytest.fixture()
def client(tmp_path: Path) -> TestClient:
    settings = Settings(
        docs_dir=tmp_path / "docs",
        index_dir=tmp_path / "index",
        artifacts_dir=tmp_path / "artifacts",
        cors_origins=["http://localhost:3000"],
    )
    app = create_app(settings=settings)
    return TestClient(app)

