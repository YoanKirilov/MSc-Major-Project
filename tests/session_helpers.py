from app.security.session import SessionManager


BASE_URL = "http://127.0.0.1:8765"


def authenticate_client(client, manager: SessionManager) -> dict[str, str]:
    response = client.post(
        "/api/session",
        json={"token": manager.bootstrap_token},
        headers={"Origin": BASE_URL},
    )
    assert response.status_code == 200, response.text
    return {
        "Origin": BASE_URL,
        "X-CSRF-Token": response.json()["csrf_token"],
    }
