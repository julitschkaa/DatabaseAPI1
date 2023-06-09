import pytest
from starlette.testclient import TestClient

from main import app

from fastapi import FastAPI

appi = FastAPI()

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}
