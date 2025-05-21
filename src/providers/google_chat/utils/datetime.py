"""
Datetime utilities for Google Chat API.
"""
import datetime
from typing import Optional, Union


def rfc3339_format(dt: datetime.datetime) -> str:
    """
    Format a datetime object as RFC 3339 format suitable for Google Chat API filter strings.
    
    The Google Chat API requires RFC 3339 format for createTime filters.
    Messages in Google Chat typically have createTime in this format: "2025-05-13T16:58:05.935391Z"
    This function ensures proper formatting with microsecond precision and Z timezone indicator.
    
    Args:
        dt: The datetime object to format, should be timezone-aware (UTC)
        
    Returns:
        RFC 3339 formatted string suitable for Google Chat API filters
    """
    # Ensure timezone info is UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    
    # Format with microsecond precision, handling trailing zeros properly
    formatted_time = dt.strftime("%Y-%m-%dT%H:%M:%S.%f").rstrip('0').rstrip('.')
    
    # Ensure Z suffix for UTC timezone (RFC 3339 format)
    if dt.tzinfo == datetime.timezone.utc:
        return f"{formatted_time}Z"
    else:
        # If not UTC (unlikely case), use offset format
        return dt.isoformat()


def parse_date(date_input: Union[str, datetime.datetime], default_time: str = "start") -> datetime.datetime:
    """
    Parse a date input to a timezone-aware UTC datetime.
    
    Args:
        date_input: Either a string in YYYY-MM-DD format or a datetime object
        default_time: Either 'start' for beginning of day or 'end' for end of day
        
    Returns:
        Timezone-aware datetime object
        
    Raises:
        ValueError: If date string is not in YYYY-MM-DD format
    """
    # If already a datetime object, just use it
    if isinstance(date_input, datetime.datetime):
        dt = date_input
    else:
        try:
            dt = datetime.datetime.strptime(date_input, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Date '{date_input}' must be in YYYY-MM-DD format")
    
    # Add time component based on default_time
    if default_time == "start":
        dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    elif default_time == "end":
        dt = dt.replace(hour=23, minute=59, second=59, microsecond=999999)
        
    # Always add UTC timezone info
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
        
    return dt


def create_date_filter(start_date: Union[str, datetime.datetime, None], 
                      end_date: Union[str, datetime.datetime, None] = None) -> Optional[str]:
    """
    Create an API filter string for date ranges that works with Google Chat API.
    
    NOTE: The Google Chat API requires quotes around RFC 3339 timestamp values in filter expressions.
    This function properly formats the filter string with quotes to ensure compatibility.
    
    Example formats:
        - Single date: 'createTime > "2024-05-01T00:00:00Z"'
        - Date range: 'createTime > "2024-05-01T00:00:00Z" AND createTime < "2024-05-31T23:59:59.999999Z"'
    
    Args:
        start_date: Start date (YYYY-MM-DD string or datetime object)
        end_date: Optional end date (YYYY-MM-DD string or datetime object)
        
    Returns:
        Filter string suitable for the Google Chat API with properly quoted timestamp values
        
    Raises:
        ValueError: If dates are in incorrect format
    """
    if not start_date:
        return None
        
    # Parse start date (beginning of day)
    start_dt = parse_date(start_date, "start")
    start_formatted = rfc3339_format(start_dt)
    
    if end_date:
        # Parse end date (end of day)
        end_dt = parse_date(end_date, "end") 
        end_formatted = rfc3339_format(end_dt)
        
        # Create filter with both start and end dates
        # Google Chat API requires quotes around timestamp values
        return f'createTime > "{start_formatted}" AND createTime < "{end_formatted}"'
    else:
        # Only start date provided - just filter for messages after this date
        # This allows finding ALL messages from the start date onwards
        return f'createTime > "{start_formatted}"' 