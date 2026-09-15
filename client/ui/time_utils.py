from datetime import datetime, timezone


def format_local_datetime(value: str | datetime | None, date_format: str = "%Y-%m-%d %H:%M") -> str:
    if value is None:
        return ""
    try:
        parsed = value if isinstance(value, datetime) else datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone().strftime(date_format)
    except (TypeError, ValueError):
        return str(value)