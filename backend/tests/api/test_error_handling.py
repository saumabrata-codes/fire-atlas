
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import create_app
from app.core.exceptions import (
    BadRequestException,
    DataUnavailableException,
)


@pytest.fixture
def client():
    app: FastAPI = create_app()

    # Temporary routes used only to test exception handling.
    async def bad_request_endpoint():
        raise BadRequestException(
            message="Invalid geographic filter.",
            code="INVALID_GEOGRAPHIC_FILTER",
        )

    async def unavailable_endpoint():
        raise DataUnavailableException()

    async def unexpected_error_endpoint():
        raise ValueError("Internal test error")

    async def validation_endpoint(quantity: int):
        return {"quantity": quantity}

    app.add_api_route(
        "/test/bad-request",
        bad_request_endpoint,
        methods=["GET"],
    )

    app.add_api_route(
        "/test/unavailable",
        unavailable_endpoint,
        methods=["GET"],
    )

    app.add_api_route(
        "/test/unexpected",
        unexpected_error_endpoint,
        methods=["GET"],
    )

    app.add_api_route(
        "/test/validation",
        validation_endpoint,
        methods=["GET"],
    )

    return TestClient(app, raise_server_exceptions=False)


def test_bad_request_returns_400(client):
    response = client.get("/test/bad-request")

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_GEOGRAPHIC_FILTER"


def test_validation_error_returns_422(client):
    response = client.get("/test/validation?quantity=invalid")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert len(response.json()["error"]["details"]) > 0


def test_data_unavailable_returns_503(client):
    response = client.get("/test/unavailable")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "DATA_UNAVAILABLE"


def test_unexpected_error_returns_500(client):
    response = client.get("/test/unexpected")

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert "Internal test error" not in response.text


def test_all_errors_use_standard_structure(client):
    response = client.get("/test/bad-request")

    body = response.json()

    assert "error" in body
    assert "code" in body["error"]
    assert "message" in body["error"]
    assert "details" in body["error"]
