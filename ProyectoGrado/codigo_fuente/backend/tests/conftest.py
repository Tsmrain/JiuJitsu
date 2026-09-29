import pytest
from fastapi.testclient import TestClient
from corpocmente.main import app

@pytest.fixture
def client():
    return TestClient(app)
