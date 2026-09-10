from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def make_client(tmp_path: Path, max_upload_size: int = 1024 * 1024) -> TestClient:
    app = create_app(
        Settings(
            data_dir=tmp_path,
            max_upload_size=max_upload_size,
            secret_key="test-secret-for-shared-file-server",
            default_admin_username="admin",
            default_admin_password="admin123",
        )
    )
    return TestClient(app)


def auth_headers(client: TestClient, username: str = "admin", password: str = "admin123") -> dict[str, str]:
    response = client.post("/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_user(client: TestClient, username: str, password: str, role: str = "user") -> dict:
    response = client.post(
        "/auth/users",
        json={"username": username, "password": password, "role": role},
        headers=auth_headers(client),
    )
    assert response.status_code == 201
    return response.json()


def test_health(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_login_and_me(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    headers = auth_headers(client)

    response = client.get("/auth/me", headers=headers)

    assert response.status_code == 200
    assert response.json()["username"] == "admin"
    assert response.json()["role"] == "admin"


def test_upload_list_search_download_delete_flow(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    headers = auth_headers(client)
    content = b"hello shared file server"

    upload_response = client.post(
        "/files/upload",
        files={"file": ("hello.txt", content, "text/plain")},
        data={"visibility": "shared"},
        headers=headers,
    )
    assert upload_response.status_code == 201
    uploaded = upload_response.json()
    assert uploaded["original_name"] == "hello.txt"
    assert uploaded["size"] == len(content)
    assert uploaded["content_type"] == "text/plain"
    assert uploaded["visibility"] == "shared"
    assert uploaded["owner_name"] == "admin"

    list_response = client.get("/files", headers=headers)
    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()] == [uploaded["id"]]

    search_response = client.get("/files/search?q=hello", headers=headers)
    assert search_response.status_code == 200
    assert [item["id"] for item in search_response.json()] == [uploaded["id"]]

    download_response = client.get(f"/files/{uploaded['id']}/download", headers=headers)
    assert download_response.status_code == 200
    assert download_response.content == content
    assert "hello.txt" in download_response.headers["content-disposition"]

    delete_response = client.delete(f"/files/{uploaded['id']}", headers=headers)
    assert delete_response.status_code == 204

    assert client.get("/files", headers=headers).json() == []
    assert client.get(f"/files/{uploaded['id']}/download", headers=headers).status_code == 404


def test_file_apis_require_login(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    response = client.get("/files")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "NOT_AUTHENTICATED"


def test_private_file_is_hidden_from_other_users(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    create_user(client, "alice", "alice123")
    create_user(client, "bob", "bob123")
    alice_headers = auth_headers(client, "alice", "alice123")
    bob_headers = auth_headers(client, "bob", "bob123")

    upload_response = client.post(
        "/files/upload",
        files={"file": ("secret.txt", b"private", "text/plain")},
        data={"visibility": "private"},
        headers=alice_headers,
    )
    assert upload_response.status_code == 201
    file_id = upload_response.json()["id"]

    assert client.get("/files", headers=bob_headers).json() == []
    assert client.get(f"/files/{file_id}/download", headers=bob_headers).status_code == 404
    assert client.delete(f"/files/{file_id}", headers=bob_headers).status_code == 404

    alice_delete = client.delete(f"/files/{file_id}", headers=alice_headers)
    assert alice_delete.status_code == 204


def test_shared_file_can_be_downloaded_but_not_deleted_by_other_user(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    create_user(client, "alice", "alice123")
    create_user(client, "bob", "bob123")
    alice_headers = auth_headers(client, "alice", "alice123")
    bob_headers = auth_headers(client, "bob", "bob123")

    upload_response = client.post(
        "/files/upload",
        files={"file": ("shared.txt", b"shared", "text/plain")},
        data={"visibility": "shared"},
        headers=alice_headers,
    )
    file_id = upload_response.json()["id"]

    assert client.get(f"/files/{file_id}/download", headers=bob_headers).status_code == 200
    delete_response = client.delete(f"/files/{file_id}", headers=bob_headers)
    assert delete_response.status_code == 403
    assert delete_response.json()["error"]["code"] == "PERMISSION_DENIED"


def test_unknown_file_returns_structured_error(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    response = client.get("/files/missing/download", headers=auth_headers(client))

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "FILE_NOT_FOUND"


def test_upload_size_limit_removes_temp_file(tmp_path: Path) -> None:
    client = make_client(tmp_path, max_upload_size=4)

    response = client.post(
        "/files/upload",
        files={"file": ("too-big.bin", b"12345", "application/octet-stream")},
        headers=auth_headers(client),
    )

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "FILE_TOO_LARGE"
    assert client.get("/files", headers=auth_headers(client)).json() == []
    storage_dir = tmp_path / "storage"
    assert [path for path in storage_dir.glob("*") if path.name != ".tmp"] == []
    assert not any((storage_dir / ".tmp").glob("*"))


def test_path_like_upload_name_is_sanitized(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    response = client.post(
        "/files/upload",
        files={"file": ("../../evil.txt", b"safe", "text/plain")},
        headers=auth_headers(client),
    )

    assert response.status_code == 201
    assert response.json()["original_name"] == "evil.txt"
    assert not (tmp_path / "evil.txt").exists()


def test_admin_can_view_operation_logs(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    headers = auth_headers(client)

    upload_response = client.post(
        "/files/upload",
        files={"file": ("log-demo.txt", b"log", "text/plain")},
        headers=headers,
    )
    file_id = upload_response.json()["id"]
    assert client.get(f"/files/{file_id}/download", headers=headers).status_code == 200
    assert client.delete(f"/files/{file_id}", headers=headers).status_code == 204

    logs_response = client.get("/logs", headers=headers)

    assert logs_response.status_code == 200
    actions = [item["action"] for item in logs_response.json()]
    assert "upload" in actions
    assert "download" in actions
    assert "delete" in actions


def test_only_admin_can_view_logs(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    create_user(client, "alice", "alice123")
    alice_headers = auth_headers(client, "alice", "alice123")

    response = client.get("/logs", headers=alice_headers)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"
