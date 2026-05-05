import pytest

# Auth email/mot de passe est desactivee : Spotify est le seul mecanisme de login.
# Les use cases sont conserves, mais les routes /register et /login ne sont plus exposees.
pytestmark = pytest.mark.skip(reason="Email/password auth disabled, Spotify-only login")

AUTH = "/api/v1/auth"

VALID_PAYLOAD = {
    "first_name": "Alex",
    "last_name": "K",
    "email": "alex@example.com",
    "password": "Aa1!aaaa",
}


def test_register_returns_tokens(client):
    res = client.post(f"{AUTH}/register", json=VALID_PAYLOAD)

    assert res.status_code == 201
    body = res.get_json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


def test_register_rejects_duplicate_email(client):
    client.post(f"{AUTH}/register", json=VALID_PAYLOAD)
    res = client.post(f"{AUTH}/register", json=VALID_PAYLOAD)

    assert res.status_code == 409
    assert res.get_json()["error"] == "user_already_exists"


def test_register_rejects_weak_password(client):
    payload = {**VALID_PAYLOAD, "email": "weak@example.com", "password": "short"}
    res = client.post(f"{AUTH}/register", json=payload)

    assert res.status_code == 422


def test_login_with_correct_credentials(client):
    client.post(f"{AUTH}/register", json=VALID_PAYLOAD)

    res = client.post(f"{AUTH}/login", json={
        "email": VALID_PAYLOAD["email"],
        "password": VALID_PAYLOAD["password"],
    })

    assert res.status_code == 200
    assert "access_token" in res.get_json()


def test_login_with_wrong_password(client):
    client.post(f"{AUTH}/register", json=VALID_PAYLOAD)

    res = client.post(f"{AUTH}/login", json={
        "email": VALID_PAYLOAD["email"],
        "password": "Wrong1!aaa",
    })

    assert res.status_code == 401
    assert res.get_json()["error"] == "invalid_credentials"


def test_login_with_unknown_email(client):
    res = client.post(f"{AUTH}/login", json={
        "email": "nobody@example.com",
        "password": "Whatever1!",
    })

    assert res.status_code == 401


def test_refresh_rotates_token(client):
    register = client.post(f"{AUTH}/register", json=VALID_PAYLOAD)
    old_refresh = register.get_json()["refresh_token"]

    res = client.post(f"{AUTH}/refresh", json={"refresh_token": old_refresh})

    assert res.status_code == 200
    new_refresh = res.get_json()["refresh_token"]
    assert new_refresh != old_refresh

    # L'ancien refresh token est revoque, ne marche plus
    res2 = client.post(f"{AUTH}/refresh", json={"refresh_token": old_refresh})
    assert res2.status_code == 401


def test_logout_revokes_refresh_token(client):
    register = client.post(f"{AUTH}/register", json=VALID_PAYLOAD)
    refresh_token = register.get_json()["refresh_token"]

    logout = client.post(f"{AUTH}/logout", json={"refresh_token": refresh_token})
    assert logout.status_code == 204

    # Apres logout, le refresh token n'est plus utilisable
    res = client.post(f"{AUTH}/refresh", json={"refresh_token": refresh_token})
    assert res.status_code == 401
