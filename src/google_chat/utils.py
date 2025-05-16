import datetime
import re
from typing import Optional, Any, Dict, List


def parse_space_name(space_name: str) -> str:
    """Ensure a space name is in 'spaces/{id}' format."""
    if not space_name:
        raise ValueError("space_name cannot be empty")
    if not space_name.startswith("spaces/"):
        return f"spaces/{space_name}"
    return space_name

def parse_message_name(message_name: str) -> str:
    """Ensure a message name is in 'spaces/{space_id}/messages/{message_id}' format."""
    if not message_name:
        raise ValueError("message_name cannot be empty")
    if not message_name.startswith("spaces/"):
        raise ValueError("message_name must be in format 'spaces/{space_id}/messages/{message_id}'")
    return message_name

def parse_date(date_str: Optional[str], default_time: str = "start") -> Optional[datetime.datetime]:
    """
    Parse a YYYY-MM-DD string to a timezone-aware UTC datetime.
    default_time: 'start' = 00:00:00, 'end' = 23:59:59.999999
    """
    if not date_str:
        return None
    try:
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        if default_time == "start":
            dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        elif default_time == "end":
            dt = dt.replace(hour=23, minute=59, second=59, microsecond=999999)
        return dt.replace(tzinfo=datetime.timezone.utc)
    except ValueError:
        raise ValueError(f"Date '{date_str}' must be in YYYY-MM-DD format")

def format_pagination(page_size: Optional[int] = 50, max_size: int = 1000) -> int:
    """Clamp the page size to allowed limits."""
    if not page_size:
        return 50
    page_size = int(page_size)
    return min(max(page_size, 1), max_size)

def to_snake_case(text: str) -> str:
    """Convert a camelCase or PascalCase string to snake_case."""
    text = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", text)
    text = re.sub("([a-z0-9])([A-Z])", r"\1_\2", text)
    return text.replace("-", "_").lower()

def is_valid_email(email: str) -> bool:
    """Simple regex check for email validity."""
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))

def safe_get(d: Dict, *keys, default=None) -> Any:
    """Safely get a nested property from a dict, else default."""
    for key in keys:
        if isinstance(d, dict) and key in d:
            d = d[key]
        else:
            return default
    return d

def ensure_list(val):
    """If val is not a list, return it as a one-item list."""
    if isinstance(val, list):
        return val
    elif val is None:
        return []
    else:
        return [val]

def datetime_to_rfc3339(dt: datetime.datetime) -> str:
    """Convert a datetime object to RFC3339 string."""
    if not dt:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")

def filter_messages_by_date(messages, start: Optional[datetime.datetime], end: Optional[datetime.datetime]):
    """Filter message list by createTime within [start, end]."""
    if not (start or end):
        return messages
    filtered = []
    for msg in messages:
        create_time = msg.get("createTime")
        if not create_time:
            continue
        try:
            msg_dt = datetime.datetime.fromisoformat(create_time.replace("Z", "+00:00"))
        except Exception:
            continue
        if start and msg_dt < start:
            continue
        if end and msg_dt > end:
            continue
        filtered.append(msg)
    return filtered

def get_first_matching(items, key, value):
    """Return the first dict in items where items[key] == value, else None."""
    for item in items:
        if item.get(key) == value:
            return item
    return None

"""
General-purpose utility functions for Google Chat MCP.
"""

def isoformat_datetime(dt: datetime.datetime, with_timezone: bool = True) -> str:
    """
    Return an ISO 8601 formatted string from a datetime object.
    """
    if dt.tzinfo is None and with_timezone:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt.isoformat()


def parse_datetime(dt_str: str) -> datetime.datetime:
    """
    Parse an ISO8601 datetime string to a datetime object.
    Raises ValueError if invalid.
    """
    # Try with and without timezone
    try:
        return datetime.datetime.fromisoformat(dt_str)
    except Exception:
        # Fallback: Try parsing without microseconds/timezone
        return datetime.datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")

def safe_get(d: dict, keys: List[str], default: Any = None) -> Any:
    """
    Safely get a nested value from a dict using a list of keys.
    Example: safe_get(d, ['foo', 'bar']) -> d['foo']['bar'] if present, else default
    """
    current = d
    try:
        for k in keys:
            current = current[k]
        return current
    except (KeyError, TypeError, IndexError):
        return default

def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """
    Flatten a nested dictionary.
    Example: {'a': {'b': 1}} -> {'a.b': 1}
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def truncate_string(s: str, max_len: int = 100, ellipsis: str = "...") -> str:
    """
    Truncate a string to a maximum length, adding ellipsis if needed.
    """
    return s if len(s) <= max_len else s[:max_len - len(ellipsis)] + ellipsis

def humanize_timedelta(td: datetime.timedelta) -> str:
    """
    Convert a timedelta to a human-friendly string.
    """
    seconds = int(td.total_seconds())
    periods = [
        ('day', 86400),
        ('hour', 3600),
        ('min', 60),
        ('sec', 1),
    ]
    result = []
    for name, count in periods:
        value = seconds // count
        if value:
            seconds -= value * count
            result.append(f"{value} {name}{'s' if value > 1 else ''}")
    return ', '.join(result) if result else "0 sec"

def coalesce(*args):
    """
    Return the first non-None argument.
    """
    for arg in args:
        if arg is not None:
            return arg
    return None

def ensure_space_name(space_name: str) -> str:
    """
    Ensure a space_name starts with 'spaces/'.
    """
    return space_name if space_name.startswith('spaces/') else f"spaces/{space_name}"

# Add more general-purpose helpers as needed below...


