"""
Wrappers and utilities for Google People API.
Handles user info lookup, batch fetching, and normalization.
"""

from typing import Optional, List, Dict
import logging

# You’ll need the actual Google API client library for these.
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

logger = logging.getLogger("google_chat.people_api")

def get_people_service(credentials: Credentials):
    """Return an authorized People API service instance."""
    return build("people", "v1", credentials=credentials, cache_discovery=False)

def get_user_profile(user_id: str, credentials: Credentials) -> Optional[Dict]:
    """
    Get a user's People API profile by resource name or userId.
    Args:
        user_id: Format can be 'people/XYZ', 'users/XYZ', or plain userId.
        credentials: Authorized Google OAuth credentials.
    Returns:
        Dictionary with user info (email, display name, profile photo, etc.), or None if not found.
    """
    service = get_people_service(credentials)
    # Normalize resource name
    resource_name = user_id
    if not (user_id.startswith("people/") or user_id.startswith("users/")):
        resource_name = f"people/{user_id}"

    try:
        person = service.people().get(
            resourceName=resource_name,
            personFields="emailAddresses,names,photos"
        ).execute()
        return _parse_person_info(person)
    except Exception as e:
        logger.warning(f"Could not fetch user profile for {user_id}: {e}")
        return None

def batch_get_user_profiles(user_ids: List[str], credentials: Credentials) -> List[Dict]:
    """
    Batch fetch People API user profiles.
    Args:
        user_ids: List of user IDs ('people/XYZ', etc.)
        credentials: OAuth credentials.
    Returns:
        List of user info dicts (some may be None if not found).
    """
    service = get_people_service(credentials)
    resource_names = [
        uid if uid.startswith("people/") else f"people/{uid}" for uid in user_ids
    ]
    try:
        response = service.people().getBatchGet(
            resourceNames=resource_names,
            personFields="emailAddresses,names,photos"
        ).execute()
        people = response.get("responses", [])
        return [
            _parse_person_info(p.get("person")) if "person" in p else None
            for p in people
        ]
    except Exception as e:
        logger.error(f"Batch get failed: {e}")
        return []

def _parse_person_info(person: Dict) -> Dict:
    """Extract normalized info from a People API person response."""
    if not person:
        return {}
    names = person.get("names", [{}])[0]
    emails = person.get("emailAddresses", [{}])[0]
    photos = person.get("photos", [{}])[0]
    return {
        "id": person.get("resourceName"),
        "display_name": names.get("displayName"),
        "given_name": names.get("givenName"),
        "family_name": names.get("familyName"),
        "email": emails.get("value"),
        "profile_photo": photos.get("url"),
    }

def get_user_email(person: Dict) -> Optional[str]:
    """Get the primary email from parsed person info dict."""
    return person.get("email") if person else None

def get_user_display_name(person: Dict) -> Optional[str]:
    """Get the display name from parsed person info dict."""
    return person.get("display_name") if person else None

# Add more utilities as needed (profile photo fallback, normalization, etc.)

