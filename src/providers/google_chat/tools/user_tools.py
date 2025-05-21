from src.providers.google_chat.api.auth import get_user_info_by_id, get_current_user_info
from src.mcp_instance import mcp


@mcp.tool()
async def get_my_user_info_tool() -> dict:
    """Get information about the currently authenticated user.

    Uses the Google People API (people.get method) to retrieve profile information
    about the currently authenticated user. This is useful for personalizing interactions,
    displaying user information, or determining user permissions.

    This tool requires OAuth authentication with people.* scope permissions.
    It retrieves user details including display name, email, and name components.

    Returns:
        dictionary containing user details such as:
        - email: The primary email address of the authenticated user (string)
        - display_name: The full display name of the user (string)
        - given_name: The user's first or given name (string)
        - family_name: The user's last or family name (string)

    Note that all fields might not be available depending on the user's privacy settings
    and the permissions granted to the application.

    API Reference:
        https://developers.google.com/people/api/rest/v1/people/get
    """

    return await get_current_user_info()


@mcp.tool()
async def get_user_info_by_id_tool(user_id: str) -> dict:
    """Get information about a specific user by their user ID.

    Uses the Google People API to retrieve detailed profile information about a specific user
    identified by their ID. This helps to show user details when displaying messages or mentions,
    enabling personalized interactions in the Chat interface.

    This tool requires OAuth authentication with appropriate people.* scope permissions.
    It attempts to convert user IDs from Chat API format to People API format if necessary.

    Args:
        user_id: The ID of the user to get information for. This can be in several formats:
               - Google Chat format: 'users/1234567890'
               - People API format: 'people/1234567890'
               - Raw ID: '1234567890'
               The function will attempt to convert between formats as needed.

    Returns:
        dictionary containing user details such as:
        - id: The original user ID provided (string)
        - email: The user's primary email address, if available (string or null)
        - display_name: The full display name of the user (string)
        - given_name: The user's first name, if available (string or null)
        - family_name: The user's last name, if available (string or null)
        - profile_photo: URL to the user's profile photo, if available (string or null)
        - error: Error description if user info retrieval fails but basic info is returned

    Note: If detailed information cannot be retrieved due to permissions or other issues,
    basic information will still be returned with the user ID and a generic display name.

    API Reference:
        https://developers.google.com/people/api/rest/v1/people/get
    """
    return await get_user_info_by_id(user_id)