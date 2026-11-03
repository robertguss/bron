from collections.abc import Callable
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from bron.dts.app import create_app

BASE = "http://testserver/api/dts"
RESOURCE = "urn:cts:bron:fixture.gd.ed1"

Client = Callable[[Path], TestClient]


@pytest.fixture
def serve() -> Client:
    """A test client for the resolver over `repo`, following no redirects."""

    def make(repo: Path) -> TestClient:
        return TestClient(create_app(repo, base_url=BASE), follow_redirects=False)

    return make


@pytest.fixture
def client(serve: Client, data_repo: Path) -> TestClient:
    return serve(data_repo)
