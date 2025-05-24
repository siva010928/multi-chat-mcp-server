import datetime
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from src.mcp_core.engine.provider_loader import get_provider_config_value

# Set up logger
logger = logging.getLogger(__name__)

# Provider name
PROVIDER_NAME = "google_chat"

# Get configuration values
DEFAULT_TOKEN_PATH = get_provider_config_value(
    PROVIDER_NAME, 
    "token_path"
)
SCOPES = get_provider_config_value(
    PROVIDER_NAME, 
    "scopes"
)

logger.info(f"Using configuration for provider: {PROVIDER_NAME}")
logger.info(f"Token path: {DEFAULT_TOKEN_PATH}")
logger.info(f"Scopes: {SCOPES}")

# Ensure token path is absolute
if not os.path.isabs(DEFAULT_TOKEN_PATH):
    # Convert to absolute path relative to the project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../'))
    DEFAULT_TOKEN_PATH = os.path.join(project_root, DEFAULT_TOKEN_PATH)
    logger.info(f"Converted token path to absolute path: {DEFAULT_TOKEN_PATH}")

# Use a module-level dictionary to store token info
# This ensures it's shared across all imports of this module
if not hasattr(sys.modules[__name__], '_token_info'):
    setattr(sys.modules[__name__], '_token_info', {
        'credentials': None,
        'last_refresh': None,
        'token_path': DEFAULT_TOKEN_PATH
    })
    logger.info(f"Initialized _token_info with token_path: {getattr(sys.modules[__name__], '_token_info')['token_path']}")

# Create a property to access the module-level token_info
def get_token_info() -> Dict[str, Any]:
    return getattr(sys.modules[__name__], '_token_info')

# For backward compatibility
token_info = get_token_info()


def set_token_path(path: str) -> None:
    """Set the global token path for OAuth storage.

    Args:
        path: Path where the token should be stored
    """
    # Use the module-level token_info
    token_info = get_token_info()
    token_info['token_path'] = path
    logger.info(f"Token path set to: {path}")


def save_credentials(creds: Credentials, token_path: Optional[str] = None) -> None:
    """Save credentials to file and update in-memory cache.

    Args:
        creds: The credentials to save
        token_path: Path to save the token file
    """
    # Use the module-level token_info
    token_info = get_token_info()

    # Use configured token path if none provided
    if token_path is None:
        token_path = token_info['token_path']

    # Save to file
    token_path = Path(token_path)
    logger.info(f"Saving credentials to file: {token_path}")
    with open(token_path, 'w') as token:
        token.write(creds.to_json())

    # Update in-memory cache
    token_info['credentials'] = creds
    token_info['last_refresh'] = datetime.datetime.utcnow()
    logger.info(f"Updated in-memory credentials cache")


def get_credentials(token_path: Optional[str] = None) -> Optional[Credentials]:
    """Gets valid user credentials from storage or memory.

    Args:
        token_path: Optional path to token file. If None, uses the configured path.

    Returns:
        Credentials object or None if no valid credentials exist
    """
    import logging
    logger = logging.getLogger(__name__)

    # Use the module-level token_info
    token_info = get_token_info()

    if token_path is None:
        token_path = token_info['token_path']

    logger.info(f"Getting credentials from token path: {token_path}")

    creds = token_info['credentials']
    logger.info(f"Credentials in memory: {creds is not None}")

    # If no credentials in memory, try to load from file
    if not creds:
        token_path = Path(token_path)
        logger.info(f"Token path exists: {token_path.exists()}")
        if token_path.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
                token_info['credentials'] = creds
                logger.info(f"Loaded credentials from file: {creds is not None}")
                logger.info(f"Credentials valid: {creds.valid if creds else None}")
                logger.info(f"Credentials expired: {creds.expired if creds else None}")
                logger.info(f"Credentials has refresh token: {bool(creds.refresh_token) if creds else None}")
            except Exception as e:
                logger.error(f"Error loading credentials from file: {str(e)}")
                return None

    # If we have credentials that need refresh
    if creds and creds.expired and creds.refresh_token:
        logger.info("Refreshing expired credentials")
        try:
            creds.refresh(Request())
            save_credentials(creds, token_path)
            logger.info("Credentials refreshed successfully")
        except Exception as e:
            logger.error(f"Error refreshing credentials: {str(e)}")
            return None

    result = creds if (creds and creds.valid) else None
    logger.info(f"Returning credentials: {result is not None}")
    return result


async def refresh_token(token_path: Optional[str] = None) -> tuple[bool, str]:
    """Attempt to refresh the current token.

    Args:
        token_path: Path to the token file. If None, uses the configured path.

    Returns:
        Tuple of (success: bool, message: str)
    """
    # Use the module-level token_info
    token_info = get_token_info()

    if token_path is None:
        token_path = token_info['token_path']

    try:
        creds = token_info['credentials']
        if not creds:
            token_path = Path(token_path)
            if not token_path.exists():
                return False, "No token file found"
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

        if not creds.refresh_token:
            return False, "No refresh token available"

        creds.refresh(Request())
        save_credentials(creds, token_path)
        return True, "Token refreshed successfully"
    except Exception as e:
        return False, f"Failed to refresh token: {str(e)}"


async def get_current_user_info() -> dict:
    """Gets information about the currently authenticated user.

    Returns:
        Dictionary containing user details

    Raises:
        Exception: If authentication fails or user info retrieval fails
    """
    try:
        creds = get_credentials()
        if not creds:
            raise Exception(f"No valid credentials found. Please authenticate first at {DEFAULT_TOKEN_PATH}")

        # Use the People API to get user information
        people_service = build('people', 'v1', credentials=creds)

        # Get profile data for the authenticated user
        profile = people_service.people().get(
            resourceName='people/me',
            personFields='names,emailAddresses'
        ).execute()

        # Extract the user's display name and email
        names = profile.get('names', [])
        emails = profile.get('emailAddresses', [])

        user_info = {
            "email": emails[0].get("value") if emails else None,
            "display_name": names[0].get("displayName") if names else None,
            "given_name": names[0].get("givenName") if names else None,
            "family_name": names[0].get("familyName") if names else None
        }

        return user_info

    except Exception as e:
        raise Exception(f"Failed to get user info: {str(e)}")


async def get_user_info_by_id(user_id: str) -> dict:
    """Gets information about a specific user by their user ID.

    Args:
        user_id: The ID of the user to get information for (e.g., 'users/1234567890')

    Returns:
        Dictionary containing user details if available

    Raises:
        Exception: If authentication fails or user info retrieval fails
    """
    try:
        creds = get_credentials()
        if not creds:
            raise Exception(f"No valid credentials found. Please authenticate first at {DEFAULT_TOKEN_PATH}")

        # Use the People API to get user information
        people_service = build('people', 'v1', credentials=creds)

        # Extract user resource name from user_id if needed
        if not user_id.startswith('people/'):
            # Convert from Chat API format (users/123) to People API format (people/123)
            if user_id.startswith('users/'):
                user_resource = f"people/{user_id.split('/')[1]}"
            else:
                user_resource = f"people/{user_id}"
        else:
            user_resource = user_id

        try:
            # Try to get profile data for the user
            profile = people_service.people().get(
                resourceName=user_resource,
                personFields='names,emailAddresses,photos'
            ).execute()

            # Extract user information
            names = profile.get('names', [])
            emails = profile.get('emailAddresses', [])
            photos = profile.get('photos', [])

            user_info = {
                "id": user_id,
                "email": emails[0].get("value") if emails else None,
                "display_name": names[0].get("displayName") if names else None,
                "given_name": names[0].get("givenName") if names else None,
                "family_name": names[0].get("familyName") if names else None,
                "profile_photo": photos[0].get("url") if photos else None
            }

            return user_info
        except Exception as e:
            # If we can't get detailed info, return basic info
            return {
                "id": user_id,
                "display_name": f"User {user_id.split('/')[-1]}",
                "error": str(e)
            }

    except Exception as e:
        raise Exception(f"Failed to get user info: {str(e)}")
