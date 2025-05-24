from src.providers.google_chat.api.auth import get_user_info_by_id, get_current_user_info
from src.mcp_instance import mcp


@mcp.tool()
async def get_my_user_info_tool() -> dict:
    """Get information about the currently authenticated user.

    Uses the Google People API (people.get method) to retrieve profile information
    about the currently authenticated user. This is useful for personalizing interactions,
    displaying user information, or determining user permissions.

    COMMON USE CASES:
    - Personalizing responses with the user's name
    - Including the user's email in API requests that require user identification
    - Verifying the current user's identity before performing sensitive operations
    - Creating personalized reports or summaries for the current user
    
    BENEFITS OF USING THIS TOOL:
    - Ensures messages and operations are correctly associated with the current user
    - Provides a consistent way to refer to the user by name
    - Helps make interactions more personal and contextual
    - Used by other tools that need to identify the current user

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
    
    Examples:
    
    1. Basic usage - get current user info:
       ```python
       user_info = get_my_user_info_tool()
       print(f"Hello, {user_info['given_name']}!")
       ```
       
    2. Use current user's email for personalized filtering:
       ```python
       # Get the current user's email
       user_info = get_my_user_info_tool()
       user_email = user_info.get("email")
       
       # Use it to find messages specifically relevant to the current user
       if user_email:
           results = search_messages_tool(
               query=f"{user_email}",
               search_mode="regex"
           )
       ```
       
    3. Personalize message responses:
       ```python
       # First get user info
       user_info = get_my_user_info_tool()
       display_name = user_info.get("display_name", "there")
       
       # Then send a personalized message
       send_message_tool(
           space_name="spaces/AAQAtjsc9v4",
           text=f"Hello {display_name}! Here's the information you requested..."
       )
       ```
       
    4. Combine with get_conversation_participants_tool to check if the current user is part of a conversation:
       ```python
       # Get current user info
       my_info = get_my_user_info_tool()
       my_email = my_info.get("email")
       
       # Get participants in a conversation
       participants = get_conversation_participants_tool(
           space_name="spaces/AAQAtjsc9v4",
           days_window=7
       )
       
       # Check if current user has participated
       user_participated = any(p.get("email") == my_email for p in participants if p.get("email"))
       ```

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

    COMMON USE CASES:
    - Getting contact information for a user who sent a message
    - Converting user IDs to human-readable names and emails
    - Extracting profile information from message sender fields
    - Building user directories or contact lists
    - Creating personalized responses that reference other users

    This tool requires OAuth authentication with appropriate people.* scope permissions.
    It attempts to convert user IDs from Chat API format to People API format if necessary.

    Args:
        user_id: The ID of the user to get information for. This can be in several formats:
               - Google Chat format: 'users/1234567890'
               - People API format: 'people/1234567890'
               - Raw ID: '1234567890'
               The function will attempt to convert between formats as needed.
               
               OBTAINING USER IDS:
               - From message objects via the 'sender.name' field
               - From participant lists via the 'id' field
               - From @mentions in message text
               
               FORMAT HANDLING:
               This tool automatically handles different ID formats, so you can directly 
               use IDs as they appear in API responses without manual formatting.

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
    
    Examples:
    
    1. Basic usage - get user info by ID:
       ```python
       user_info = get_user_info_by_id_tool(user_id="users/1234567890")
       print(f"User email: {user_info.get('email')}")
       ```
       
    2. Get user info from a message sender:
       ```python
       # First, get a message
       message = get_chat_message_tool(message_name="spaces/AAQAtjsc9v4/messages/MESSAGE_ID")
       
       # Extract the sender ID
       sender_id = message.get("sender", {}).get("name")
       
       # Get detailed info about the sender
       if sender_id:
           sender_info = get_user_info_by_id_tool(user_id=sender_id)
           sender_email = sender_info.get("email")
           sender_name = sender_info.get("display_name")
       ```
       
    3. Process all participants in a conversation:
       ```python
       # Get participants in a conversation
       participants = get_conversation_participants_tool(space_name="spaces/AAQAtjsc9v4")
       
       # Get detailed information for each participant
       for participant in participants:
           user_id = participant.get("id")
           if user_id:
               detailed_info = get_user_info_by_id_tool(user_id=user_id)
               # Do something with the detailed information
               print(f"User: {detailed_info.get('display_name')}, Email: {detailed_info.get('email')}")
       ```
       
    4. Extract user information from search results:
       ```python
       # Search for messages with a specific keyword
       search_results = search_messages_tool(query="project status")
       
       # Extract unique senders
       sender_ids = set()
       for message in search_results.get("messages", []):
           sender_id = message.get("sender", {}).get("name")
           if sender_id:
               sender_ids.add(sender_id)
       
       # Get detailed info for each unique sender
       sender_details = []
       for sender_id in sender_ids:
           sender_info = get_user_info_by_id_tool(user_id=sender_id)
           sender_details.append(sender_info)
       ```

    API Reference:
        https://developers.google.com/people/api/rest/v1/people/get
    """
    return await get_user_info_by_id(user_id)