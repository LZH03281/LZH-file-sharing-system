from mimetypes import guess_type


DEFAULT_CONTENT_TYPE = "application/octet-stream"


def resolve_content_type(filename: str, supplied: str | None = None) -> str:
    normalized = (supplied or "").strip()
    if normalized and normalized.lower() != DEFAULT_CONTENT_TYPE:
        return normalized
    guessed, _ = guess_type(filename)
    return guessed or normalized or DEFAULT_CONTENT_TYPE