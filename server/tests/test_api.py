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


def create_user(
    client: TestClient,
    username: str,
    password: str,
    role: str = "user",
    headers: dict[str, str] | None = None,
) -> dict:
    response = client.post(
        "/auth/users",
        json={"username": username, "password": password, "role": role},
        headers=headers or auth_headers(client),
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


def test_public_register_creates_normal_user(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    register_response = client.post(
        "/auth/register",
        json={"username": "newuser", "password": "newuser123"},
    )

    assert register_response.status_code == 201
    assert register_response.json()["username"] == "newuser"
    assert register_response.json()["role"] == "user"

    headers = auth_headers(client, "newuser", "newuser123")
    me_response = client.get("/auth/me", headers=headers)
    assert me_response.status_code == 200
    assert me_response.json()["role"] == "user"


def test_admin_can_manage_user_status(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    admin_headers = auth_headers(client)
    user = create_user(client, "disabled_user", "disabled123")

    list_response = client.get("/auth/users", headers=admin_headers)
    assert list_response.status_code == 200
    assert any(item["username"] == "disabled_user" for item in list_response.json())

    disable_response = client.patch(
        f"/auth/users/{user['id']}/enabled",
        json={"enabled": False},
        headers=admin_headers,
    )
    assert disable_response.status_code == 200
    assert disable_response.json()["enabled"] is False

    login_response = client.post(
        "/auth/login",
        json={"username": "disabled_user", "password": "disabled123"},
    )
    assert login_response.status_code == 401

    enable_response = client.patch(
        f"/auth/users/{user['id']}/enabled",
        json={"enabled": True},
        headers=admin_headers,
    )
    assert enable_response.status_code == 200
    assert enable_response.json()["enabled"] is True


def test_admin_cannot_disable_self(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    admin_headers = auth_headers(client)
    me_response = client.get("/auth/me", headers=admin_headers)
    admin_id = me_response.json()["id"]

    response = client.patch(
        f"/auth/users/{admin_id}/enabled",
        json={"enabled": False},
        headers=admin_headers,
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "CANNOT_DISABLE_SELF"


def test_initial_admin_controls_admin_creation_limit(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    create_user(client, "admin2", "admin222", role="admin")
    create_user(client, "admin3", "admin333", role="admin")

    over_limit_response = client.post(
        "/auth/users",
        json={"username": "admin4", "password": "admin444", "role": "admin"},
        headers=auth_headers(client),
    )
    assert over_limit_response.status_code == 409
    assert over_limit_response.json()["error"]["code"] == "ADMIN_LIMIT_REACHED"

    admin2_headers = auth_headers(client, "admin2", "admin222")
    non_initial_response = client.post(
        "/auth/users",
        json={"username": "admin5", "password": "admin555", "role": "admin"},
        headers=admin2_headers,
    )
    assert non_initial_response.status_code == 403
    assert non_initial_response.json()["error"]["code"] == "PERMISSION_DENIED"


def test_non_initial_admin_can_manage_only_normal_users(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    admin2 = create_user(client, "manager", "manager123", role="admin")
    admin3 = create_user(client, "audit_admin", "audit123", role="admin")
    alice = create_user(client, "alice", "alice123")
    manager_headers = auth_headers(client, "manager", "manager123")

    disable_user_response = client.patch(
        f"/auth/users/{alice['id']}/enabled",
        json={"enabled": False},
        headers=manager_headers,
    )
    assert disable_user_response.status_code == 200
    assert disable_user_response.json()["enabled"] is False

    enable_user_response = client.patch(
        f"/auth/users/{alice['id']}/enabled",
        json={"enabled": True},
        headers=manager_headers,
    )
    assert enable_user_response.status_code == 200
    assert enable_user_response.json()["enabled"] is True

    disable_admin_response = client.patch(
        f"/auth/users/{admin2['id']}/enabled",
        json={"enabled": False},
        headers=manager_headers,
    )
    assert disable_admin_response.status_code == 400
    assert disable_admin_response.json()["error"]["code"] == "CANNOT_DISABLE_SELF"

    disable_other_admin_response = client.patch(
        f"/auth/users/{admin3['id']}/enabled",
        json={"enabled": False},
        headers=manager_headers,
    )
    assert disable_other_admin_response.status_code == 403
    assert disable_other_admin_response.json()["error"]["code"] == "PERMISSION_DENIED"

    initial_admin_id = client.get("/auth/me", headers=auth_headers(client)).json()["id"]
    delete_initial_admin_response = client.delete(
        f"/auth/users/{initial_admin_id}",
        headers=manager_headers,
    )
    assert delete_initial_admin_response.status_code == 400
    assert delete_initial_admin_response.json()["error"]["code"] == "CANNOT_DELETE_INITIAL_ADMIN"

    delete_user_response = client.delete(
        f"/auth/users/{alice['id']}",
        headers=manager_headers,
    )
    assert delete_user_response.status_code == 204
    assert client.post("/auth/login", json={"username": "alice", "password": "alice123"}).status_code == 401


def test_initial_admin_can_delete_non_initial_admin(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    admin2 = create_user(client, "admin2", "admin222", role="admin")

    response = client.delete(f"/auth/users/{admin2['id']}", headers=auth_headers(client))

    assert response.status_code == 204
    assert client.post("/auth/login", json={"username": "admin2", "password": "admin222"}).status_code == 401


def test_delete_user_transfers_files_to_initial_admin(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    alice = create_user(client, "file_owner", "owner123")
    bob = create_user(client, "bob", "bob123")
    alice_headers = auth_headers(client, "file_owner", "owner123")
    upload_response = client.post(
        "/files/upload",
        files={"file": ("owned.txt", b"owned", "text/plain")},
        data={"visibility": "private", "access_password": "Abc123"},
        headers=alice_headers,
    )
    assert upload_response.status_code == 201
    file_id = upload_response.json()["id"]

    response = client.delete(f"/auth/users/{alice['id']}", headers=auth_headers(client))

    assert response.status_code == 204
    assert client.post("/auth/login", json={"username": "file_owner", "password": "owner123"}).status_code == 401

    admin_files_response = client.get("/files", headers=auth_headers(client))
    assert admin_files_response.status_code == 200
    transferred = next(item for item in admin_files_response.json() if item["id"] == file_id)
    assert transferred["owner_name"] == "admin"
    assert transferred["visibility"] == "shared"

    bob_files_response = client.get("/files", headers=auth_headers(client, "bob", "bob123"))
    assert bob_files_response.status_code == 200
    assert any(item["id"] == file_id for item in bob_files_response.json())


def test_deleted_user_ids_are_reused_in_order(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    user2 = create_user(client, "user2", "user222")
    user3 = create_user(client, "user3", "user333")
    user4 = create_user(client, "user4", "user444")
    user5 = create_user(client, "user5", "user555")

    assert [user2["id"], user3["id"], user4["id"], user5["id"]] == [2, 3, 4, 5]

    admin_headers = auth_headers(client)
    assert client.delete(f"/auth/users/{user2['id']}", headers=admin_headers).status_code == 204
    assert client.delete(f"/auth/users/{user3['id']}", headers=admin_headers).status_code == 204

    reused2 = create_user(client, "reused2", "reused222")
    reused3 = create_user(client, "reused3", "reused333")
    next_user = create_user(client, "next_user", "next123")

    assert reused2["id"] == 2
    assert reused3["id"] == 3
    assert next_user["id"] == 6


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


def test_search_files_by_owner_id_includes_private_metadata(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    alice = create_user(client, "owner_alice", "alice123")
    create_user(client, "viewer_bob", "bob123")
    alice_headers = auth_headers(client, "owner_alice", "alice123")
    bob_headers = auth_headers(client, "viewer_bob", "bob123")

    shared_response = client.post(
        "/files/upload",
        files={"file": ("alice-shared.txt", b"shared", "text/plain")},
        data={"visibility": "shared"},
        headers=alice_headers,
    )
    private_response = client.post(
        "/files/upload",
        files={"file": ("alice-private.txt", b"private", "text/plain")},
        data={"visibility": "private", "access_password": "Abc123"},
        headers=alice_headers,
    )
    assert shared_response.status_code == 201
    assert private_response.status_code == 201

    admin_response = client.get(f"/files/search/owner?owner_id={alice['id']}", headers=auth_headers(client))
    assert admin_response.status_code == 200
    assert {item["original_name"] for item in admin_response.json()} == {
        "alice-shared.txt",
        "alice-private.txt",
    }

    bob_response = client.get(f"/files/search/owner?owner_id={alice['id']}", headers=bob_headers)
    assert bob_response.status_code == 200
    assert {item["original_name"] for item in bob_response.json()} == {
        "alice-shared.txt",
        "alice-private.txt",
    }

    alice_response = client.get(f"/files/search/owner?owner_id={alice['id']}", headers=alice_headers)
    assert alice_response.status_code == 200
    assert {item["original_name"] for item in alice_response.json()} == {
        "alice-shared.txt",
        "alice-private.txt",
    }


def test_file_apis_require_login(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    response = client.get("/files")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "NOT_AUTHENTICATED"


def test_private_file_is_visible_but_requires_password(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    create_user(client, "alice", "alice123")
    create_user(client, "bob", "bob123")
    alice_headers = auth_headers(client, "alice", "alice123")
    bob_headers = auth_headers(client, "bob", "bob123")

    upload_response = client.post(
        "/files/upload",
        files={"file": ("secret.txt", b"private", "text/plain")},
        data={"visibility": "private", "access_password": "Aa1234"},
        headers=alice_headers,
    )
    assert upload_response.status_code == 201
    file_id = upload_response.json()["id"]

    bob_files = client.get("/files", headers=bob_headers).json()
    assert [item["id"] for item in bob_files] == [file_id]

    no_password_response = client.get(f"/files/{file_id}/download", headers=bob_headers)
    assert no_password_response.status_code == 403
    assert no_password_response.json()["error"]["code"] == "PRIVATE_PASSWORD_REQUIRED"

    wrong_password_response = client.get(
        f"/files/{file_id}/download?access_password=bad123",
        headers=bob_headers,
    )
    assert wrong_password_response.status_code == 403
    assert wrong_password_response.json()["error"]["code"] == "INVALID_PRIVATE_PASSWORD"

    assert client.get(
        f"/files/{file_id}/download?access_password=Aa1234",
        headers=bob_headers,
    ).status_code == 200
    assert client.delete(f"/files/{file_id}", headers=bob_headers).status_code == 403

    assert client.get(f"/files/{file_id}/download", headers=auth_headers(client)).status_code == 200

    alice_delete = client.delete(f"/files/{file_id}", headers=alice_headers)
    assert alice_delete.status_code == 204


def test_private_upload_requires_six_alnum_password(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    headers = auth_headers(client)

    missing_password_response = client.post(
        "/files/upload",
        files={"file": ("secret.txt", b"private", "text/plain")},
        data={"visibility": "private"},
        headers=headers,
    )
    assert missing_password_response.status_code == 400
    assert missing_password_response.json()["error"]["code"] == "INVALID_PRIVATE_PASSWORD"

    invalid_password_response = client.post(
        "/files/upload",
        files={"file": ("secret.txt", b"private", "text/plain")},
        data={"visibility": "private", "access_password": "abc-12"},
        headers=headers,
    )
    assert invalid_password_response.status_code == 400
    assert invalid_password_response.json()["error"]["code"] == "INVALID_PRIVATE_PASSWORD"


def test_non_initial_admin_needs_password_for_private_download_but_can_delete(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    create_user(client, "manager", "manager123", role="admin")
    create_user(client, "alice_private", "alice123")
    manager_headers = auth_headers(client, "manager", "manager123")
    alice_headers = auth_headers(client, "alice_private", "alice123")

    upload_response = client.post(
        "/files/upload",
        files={"file": ("managed-private.txt", b"private", "text/plain")},
        data={"visibility": "private", "access_password": "Qq1234"},
        headers=alice_headers,
    )
    file_id = upload_response.json()["id"]

    no_password_response = client.get(f"/files/{file_id}/download", headers=manager_headers)
    assert no_password_response.status_code == 403
    assert no_password_response.json()["error"]["code"] == "PRIVATE_PASSWORD_REQUIRED"

    assert client.get(
        f"/files/{file_id}/download?access_password=Qq1234",
        headers=manager_headers,
    ).status_code == 200
    assert client.delete(f"/files/{file_id}", headers=manager_headers).status_code == 204


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
