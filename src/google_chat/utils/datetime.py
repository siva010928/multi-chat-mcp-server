"""
Datetime utilities for Google Chat API.
"""
import datetime
from typing import Optional


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


def parse_date(date_str: str, default_time: str = "start") -> datetime.datetime:
    """
    Parse a YYYY-MM-DD string to a timezone-aware UTC datetime.
    
    Args:
        date_str: Date string in YYYY-MM-DD format
        default_time: Either 'start' for beginning of day or 'end' for end of day
        
    Returns:
        Timezone-aware datetime object
        
    Raises:
        ValueError: If date string is not in YYYY-MM-DD format
    """
    try:
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        
        # Add time component based on default_time
        if default_time == "start":
            dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        elif default_time == "end":
            dt = dt.replace(hour=23, minute=59, second=59, microsecond=999999)
            
        # Always add UTC timezone info
        return dt.replace(tzinfo=datetime.timezone.utc)
    except ValueError:
        raise ValueError(f"Date '{date_str}' must be in YYYY-MM-DD format")


def create_date_filter(start_date: Optional[str], end_date: Optional[str] = None) -> Optional[str]:
    """
    Create an API filter string for date ranges that works with Google Chat API.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: Optional end date in YYYY-MM-DD format
        
    Returns:
        Filter string suitable for the Google Chat API
        
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
        return f'createTime > "{start_formatted}" AND createTime < "{end_formatted}"'
    else:
        # Just one day - calculate next day for range
        next_day_dt = start_dt + datetime.timedelta(days=1)
        next_day_formatted = rfc3339_format(next_day_dt)
        
        # Create filter for single day
        return f'createTime > "{start_formatted}" AND createTime < "{next_day_formatted}"' 