from dataclasses import replace
from types import SimpleNamespace
import subprocess

import pytest

from app.core.errors import AppError
from app.services.file_security import FileSecurityService
from test_api import make_client, auth_headers


@pytest.mark.parametrize("returncode,code,http_status", [(0, None, 201), (1, "FILE_INFECTED", 400), (2, "SCAN_UNAVAILABLE", 503)])
def test_scan_upload_result(tmp_path, monkeypatch, returncode, code, http_status):
    client = make_client(tmp_path)
    storage = client.app.state.storage_service
    storage.security = FileSecurityService(replace(storage.settings, antivirus_enabled=True))
    def run(args, **kwargs):
        assert "--alert-exceeds-max=yes" in args
        assert "--alert-encrypted=yes" in args
        assert kwargs["timeout"] == 120
        assert not list(storage.storage_dir.glob("*-*-*-*-*"))
        return SimpleNamespace(returncode=returncode)
    monkeypatch.setattr(subprocess, "run", run)
    headers = auth_headers(client)
    response = client.post("/files/upload", files={"file": ("sample.txt", b"hello")}, headers=headers)
    assert response.status_code == http_status
    assert not list(storage.tmp_dir.iterdir())
    if code:
        assert response.json()["error"]["code"] == code
        assert client.get("/files", headers=headers).json() == []
        assert list(storage.storage_dir.iterdir()) == [storage.tmp_dir]
        assert any(log["detail"] == code and log["result"] == "failed" for log in client.get("/logs", headers=headers).json())


@pytest.mark.parametrize("filename,content", [("report.EXE.txt", b"text"), ("report.docm", b"text"), ("report.txt", b"MZfake"), ("script.txt", b"#!/bin/sh"), ("image.txt", b"\x7fELF"), ("bad\u202ename.txt", b"text")])
def test_risky_upload(tmp_path, filename, content):
    client = make_client(tmp_path)
    response = client.post("/files/upload", files={"file": (filename, content)}, headers=auth_headers(client))
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "UNSAFE_FILE"
    assert not list(client.app.state.storage_service.tmp_dir.iterdir())


@pytest.mark.parametrize("error", [FileNotFoundError(), subprocess.TimeoutExpired("clamscan", 120)])
def test_scanner_unavailable(tmp_path, monkeypatch, error):
    client = make_client(tmp_path)
    storage = client.app.state.storage_service
    storage.security = FileSecurityService(replace(storage.settings, antivirus_enabled=True))
    def fail(*args, **kwargs):
        raise error
    monkeypatch.setattr(subprocess, "run", fail)
    for _ in range(2):
        response = client.post("/files/upload", files={"file": ("a.txt", b"hello")}, headers=auth_headers(client))
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "SCAN_UNAVAILABLE"
    assert not list(storage.tmp_dir.iterdir())


def test_existing_file_download_is_rescanned(tmp_path, monkeypatch):
    client = make_client(tmp_path)
    headers = auth_headers(client)
    uploaded = client.post("/files/upload", files={"file": ("a.txt", b"hello")}, headers=headers).json()
    storage = client.app.state.storage_service
    storage.security = FileSecurityService(replace(storage.settings, antivirus_enabled=True))
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: SimpleNamespace(returncode=1))
    response = client.get(f"/files/{uploaded['id']}/download", headers=headers)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "FILE_INFECTED"
    assert any(log["action"] == "download" and log["result"] == "failed" for log in client.get("/logs", headers=headers).json())


def test_busy_scanner_rejects_without_starting_process(tmp_path):
    client = make_client(tmp_path)
    storage = client.app.state.storage_service
    scanner = FileSecurityService(replace(storage.settings, antivirus_enabled=True))
    path = tmp_path / "a.txt"
    path.write_text("hello")
    scanner._slot.acquire()
    try:
        with pytest.raises(AppError) as exc:
            scanner.check(path, "a.txt")
        assert exc.value.code == "SCAN_BUSY"
    finally:
        scanner._slot.release()
