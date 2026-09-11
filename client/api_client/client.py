from pathlib import Path
from typing import Any, Callable

import requests


ProgressCallback = Callable[[int, int], None]


class ApiError(Exception):
    def __init__(self, message: str, status_code: int | None = None, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


class ApiClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000", timeout: int = 20) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.access_token: str | None = None
        self.current_user: dict[str, Any] | None = None
        self.session = requests.Session()

    def configure(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def login(self, username: str, password: str) -> dict[str, Any]:
        data = self._request(
            "POST",
            "/auth/login",
            json={"username": username, "password": password},
            auth=False,
        )
        self.access_token = data["access_token"]
        self.current_user = data["user"]
        return data

    def register(self, username: str, password: str) -> dict[str, Any]:
        return self._request(
            "POST",
            "/auth/register",
            json={"username": username, "password": password},
            auth=False,
        )

    def list_users(self) -> list[dict[str, Any]]:
        return self._request("GET", "/auth/users")

    def create_user(self, username: str, password: str, role: str = "user") -> dict[str, Any]:
        return self._request(
            "POST",
            "/auth/users",
            json={"username": username, "password": password, "role": role},
        )

    def set_user_enabled(self, user_id: int, enabled: bool) -> dict[str, Any]:
        return self._request(
            "PATCH",
            f"/auth/users/{user_id}/enabled",
            json={"enabled": enabled},
        )

    def delete_user(self, user_id: int) -> None:
        self._request("DELETE", f"/auth/users/{user_id}")

    def logout(self) -> None:
        self.access_token = None
        self.current_user = None

    def list_files(self) -> list[dict[str, Any]]:
        return self._request("GET", "/files")

    def search_files(self, query: str) -> list[dict[str, Any]]:
        return self._request("GET", "/files/search", params={"q": query})

    def search_files_by_owner_id(self, owner_id: int) -> list[dict[str, Any]]:
        return self._request("GET", "/files/search/owner", params={"owner_id": owner_id})

    def upload_file(
        self,
        path: str | Path,
        visibility: str = "shared",
        access_password: str | None = None,
        progress: ProgressCallback | None = None,
    ) -> dict[str, Any]:
        file_path = Path(path)
        if progress:
            progress(0, file_path.stat().st_size)
        with file_path.open("rb") as source:
            files = {"file": (file_path.name, source, "application/octet-stream")}
            form_data = {"visibility": visibility}
            if access_password:
                form_data["access_password"] = access_password
            data = self._request("POST", "/files/upload", files=files, data=form_data)
        if progress:
            size = file_path.stat().st_size
            progress(size, size)
        return data

    def download_file(
        self,
        file_id: str,
        target_path: str | Path,
        access_password: str | None = None,
        progress: ProgressCallback | None = None,
    ) -> None:
        params = {"access_password": access_password} if access_password else None
        response = self._raw_request("GET", f"/files/{file_id}/download", params=params, stream=True)
        total = int(response.headers.get("content-length") or 0)
        target = Path(target_path)
        tmp_target = target.with_name(target.name + ".downloading")
        downloaded = 0
        try:
            with tmp_target.open("wb") as output:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if not chunk:
                        continue
                    output.write(chunk)
                    downloaded += len(chunk)
                    if progress:
                        progress(downloaded, total)
            tmp_target.replace(target)
        except Exception:
            tmp_target.unlink(missing_ok=True)
            raise

    def delete_file(self, file_id: str) -> None:
        self._request("DELETE", f"/files/{file_id}")

    def _request(self, method: str, path: str, auth: bool = True, **kwargs: Any) -> Any:
        response = self._raw_request(method, path, auth=auth, **kwargs)
        if response.status_code == 204:
            return None
        return response.json()

    def _raw_request(self, method: str, path: str, auth: bool = True, **kwargs: Any) -> requests.Response:
        url = f"{self.base_url}{path}"
        headers = kwargs.pop("headers", {})
        if auth:
            if not self.access_token:
                raise ApiError("请先登录", 401, "NOT_AUTHENTICATED")
            headers["Authorization"] = f"Bearer {self.access_token}"

        try:
            response = self.session.request(
                method,
                url,
                headers=headers,
                timeout=self.timeout,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise ApiError(f"无法连接服务器：{exc}") from exc

        if response.status_code >= 400:
            raise self._build_error(response)
        return response

    def _build_error(self, response: requests.Response) -> ApiError:
        try:
            payload = response.json()
            error = payload.get("error", {})
            message = error.get("message") or response.text
            code = error.get("code")
        except ValueError:
            message = response.text or f"请求失败：HTTP {response.status_code}"
            code = None
        return ApiError(message, response.status_code, code)
