# server.py
import httpx
import sys
import argparse
from typing import List, Dict

from fastmcp import FastMCP
from google_chat import list_chat_spaces, DEFAULT_CALLBACK_URL, set_token_path
from server_auth import run_auth_server

# Create an MCP server
mcp = FastMCP("Demo")

# Add an addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

name = "GG"

# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"

@mcp.tool()
async def fetch_weather(city: str) -> str:
    """Fetch current weather for a city"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.weather.com/{city}"
        )
        return response.text

@mcp.tool()
async def get_ip_my_address(city: str) -> str:
    """Get IP address from outian.net"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"http://outian.net/"
        )
        return response.text

@mcp.tool()
async def get_chat_spaces() -> List[Dict]:
    """List all Google Chat spaces the bot has access to.
    
    This tool requires OAuth authentication. On first run, it will open a browser window
    for you to log in with your Google account. Make sure you have credentials.json
    downloaded from Google Cloud Console in the current directory.
    """
    return await list_chat_spaces()

@mcp.tool()
async def get_space_messages(space_name: str, 
                           start_date: str,
                           end_date: str = None) -> List[Dict]:
    """List messages from a specific Google Chat space with optional time filtering.
    
    This tool requires OAuth authentication. The space_name should be in the format
    'spaces/your_space_id'. Dates should be in YYYY-MM-DD format (e.g., '2024-03-22').
    
    When only start_date is provided, it will query messages for that entire day.
    When both dates are provided, it will query messages from start_date 00:00:00Z
    to end_date 23:59:59Z.
    
    Args:
        space_name: The name/identifier of the space to fetch messages from
        start_date: Required start date in YYYY-MM-DD format
        end_date: Optional end date in YYYY-MM-DD format
    
    Returns:
        List of message objects from the space matching the time criteria
        
    Raises:
        ValueError: If the date format is invalid or dates are in wrong order
    """
    from google_chat import list_space_messages
    from datetime import datetime, timezone

    try:
        # Parse start date and set to beginning of day (00:00:00Z)
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d').replace(
            hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc
        )
        
        # Parse end date if provided and set to end of day (23:59:59Z)
        end_datetime = None
        if end_date:
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d').replace(
                hour=23, minute=59, second=59, microsecond=999999, tzinfo=timezone.utc
            )
            
            # Validate date range
            if start_datetime > end_datetime:
                raise ValueError("start_date must be before end_date")
    except ValueError as e:
        if "strptime" in str(e):
            raise ValueError("Dates must be in YYYY-MM-DD format (e.g., '2024-03-22')")
        raise e
    
    return await list_space_messages(space_name, start_datetime, end_datetime)

@mcp.tool()
async def send_message(space_name: str, text: str) -> Dict:
    """Send a message to a Google Chat space.
    
    This tool requires OAuth authentication. It will send a text-only message 
    to the specified space.
    
    Args:
        space_name: The name/identifier of the space to send the message to (e.g., 'spaces/AAQAtjsc9v4')
        text: Text content of the message
    
    Returns:
        The created message object with message ID and other details
    """
    from google_chat import create_message
    
    if not space_name.startswith('spaces/'):
        space_name = f"spaces/{space_name}"
        
    return await create_message(space_name, text)

@mcp.tool()
async def send_card_message(space_name: str, text: str, card_title: str, card_description: str = None) -> Dict:
    """Send a message with a card to a Google Chat space.
    
    This tool requires OAuth authentication. It will send a message with both 
    text and a simple card with a title and optional description.
    
    Args:
        space_name: The name/identifier of the space to send the message to (e.g., 'spaces/AAQAtjsc9v4')
        text: Text content of the message
        card_title: Title for the card
        card_description: Optional description for the card
    
    Returns:
        The created message object with message ID and other details
    """
    from google_chat import create_message
    
    if not space_name.startswith('spaces/'):
        space_name = f"spaces/{space_name}"
    
    # Create a simple card
    card = {
        "card": {
            "header": {
                "title": card_title
            }
        }
    }
    
    # Add description if provided
    if card_description:
        card["card"]["sections"] = [{
            "widgets": [{
                "textParagraph": {
                    "text": card_description
                }
            }]
        }]
    
    return await create_message(space_name, text, [card])

@mcp.tool()
async def send_interactive_card(
    space_name: str,
    card_title: str,
    card_subtitle: str = None,
    card_image_url: str = None,
    button_text: str = None,
    button_url: str = None,
    button_action_function: str = None,
    section_header: str = None,
    section_content: str = None
) -> Dict:
    """Send an interactive card message to a Google Chat space.
    
    This tool requires OAuth authentication. It creates a card with optional
    interactive elements like buttons and sections with formatted text.
    
    Args:
        space_name: The name/identifier of the space to send the message to (e.g., 'spaces/AAQAtjsc9v4')
        card_title: Title for the card
        card_subtitle: Optional subtitle for the card
        card_image_url: Optional image URL to display in the card header
        button_text: Optional text for a button
        button_url: Optional URL for the button to open when clicked
        button_action_function: Optional function name to call when button is clicked
        section_header: Optional header for a text section
        section_content: Optional text content for a section
    
    Returns:
        The created message object with message ID and other details
    """
    from google_chat import create_interactive_card_message
    
    if not space_name.startswith('spaces/'):
        space_name = f"spaces/{space_name}"
    
    # Build sections if content provided
    sections = []
    if section_header or section_content:
        section = {}
        if section_header:
            section["header"] = section_header
        
        widgets = []
        if section_content:
            widgets.append({
                "textParagraph": {
                    "text": section_content
                }
            })
        
        if widgets:
            section["widgets"] = widgets
            sections.append(section)
    
    # Build button if provided
    buttons = []
    if button_text:
        button = {
            "text": button_text
        }
        
        # Add either URL or action function
        if button_url:
            button["onClick"] = {
                "openLink": {
                    "url": button_url
                }
            }
        elif button_action_function:
            button["onClick"] = {
                "action": {
                    "function": button_action_function
                }
            }
        
        buttons.append(button)
    
    return await create_interactive_card_message(
        space_name, 
        card_title,
        card_subtitle,
        card_image_url,
        sections,
        buttons
    )

@mcp.tool()
async def update_chat_message(message_name: str, new_text: str = None) -> Dict:
    """Update an existing message in a Google Chat space.
    
    This tool requires OAuth authentication. It can update the text content of an existing message.
    
    Args:
        message_name: The full resource name of the message to update (spaces/*/messages/*)
        new_text: New text content for the message
    
    Returns:
        The updated message object
    """
    from google_chat import update_message
    
    if not message_name.startswith('spaces/'):
        raise ValueError("message_name must be a full resource name (spaces/*/messages/*)")
        
    return await update_message(message_name, new_text)

@mcp.tool()
async def reply_to_message_thread(space_name: str, thread_key: str, text: str) -> Dict:
    """Reply to a message thread in a Google Chat space.
    
    This tool requires OAuth authentication. It will send a text message as a reply 
    to an existing thread in the specified space.
    
    Args:
        space_name: The name/identifier of the space containing the thread (e.g., 'spaces/AAQAtjsc9v4')
        thread_key: The thread key to reply to (can be found in the 'thread.name' field of a message)
        text: Text content of the reply
    
    Returns:
        The created message object with message ID and other details
    """
    from google_chat import reply_to_thread
    
    if not space_name.startswith('spaces/'):
        space_name = f"spaces/{space_name}"
        
    return await reply_to_thread(space_name, thread_key, text)

@mcp.tool()
async def get_my_mentions(days: int = 7, space_id: str = None) -> List[Dict]:
    """Get messages that mention the authenticated user from all spaces or a specific space.
    
    This tool requires OAuth authentication. It will retrieve messages where the 
    authenticated user was mentioned by username across all accessible spaces or in a specific space.
    
    Args:
        days: Number of days to look back for mentions (default: 7)
        space_id: Optional space ID to check for mentions in a specific space
    
    Returns:
        List of message objects where the user was mentioned
    """
    from google_chat import get_user_mentions
    
    return await get_user_mentions(days, space_id)

@mcp.tool()
async def get_my_user_info() -> Dict:
    """Get information about the currently authenticated user.
    
    This tool requires OAuth authentication. It retrieves user details including
    display name, email, and name components.
    
    Returns:
        Dictionary containing user details such as display_name, email, given_name, and family_name
    """
    from google_chat import get_current_user_info
    
    return await get_current_user_info()

@mcp.tool()
async def get_chat_message(message_name: str) -> Dict:
    """Get a specific message by its resource name.
    
    This tool requires OAuth authentication. It retrieves details about a specific message.
    
    Args:
        message_name: The resource name of the message (spaces/*/messages/*)
    
    Returns:
        The message object with all its details
    """
    from google_chat import get_message
    
    if not message_name.startswith('spaces/'):
        raise ValueError("message_name must be a full resource name (spaces/*/messages/*)")
        
    return await get_message(message_name)

@mcp.tool()
async def delete_chat_message(message_name: str) -> Dict:
    """Delete a message by its resource name.
    
    This tool requires OAuth authentication. It deletes a specific message.
    
    Args:
        message_name: The resource name of the message to delete (spaces/*/messages/*)
    
    Returns:
        Empty response on success
    """
    from google_chat import delete_message
    
    if not message_name.startswith('spaces/'):
        raise ValueError("message_name must be a full resource name (spaces/*/messages/*)")
        
    return await delete_message(message_name)

# Enhanced Google Chat operations

@mcp.tool()
async def search_messages(query: str, spaces: List[str] = None, max_results: int = 50) -> List[Dict]:
    """Search for messages across all spaces or specified spaces.
    
    This tool requires OAuth authentication. It searches for messages containing
    the specified query text across all spaces or a list of specified spaces.
    
    Args:
        query: The search query string
        spaces: Optional list of space names to search in. If None, searches all spaces.
        max_results: Maximum number of results to return (default: 50)
        
    Returns:
        List of message objects matching the search query
    """
    from google_chat import search_messages
    return await search_messages(query, spaces, max_results)

@mcp.tool()
async def manage_space_members(space_name: str, operation: str, user_emails: List[str]) -> Dict:
    """Manage space membership - add or remove members.
    
    This tool requires OAuth authentication. It adds or removes members from a space.
    
    Args:
        space_name: The name/identifier of the space (e.g., 'spaces/AAQAtjsc9v4')
        operation: Either 'add' or 'remove'
        user_emails: List of user email addresses to add or remove
        
    Returns:
        Response with information about successful and failed operations
    """
    from google_chat import manage_space_members
    return await manage_space_members(space_name, operation, user_emails)

@mcp.tool()
async def add_emoji_reaction(message_name: str, emoji: str) -> Dict:
    """Add an emoji reaction to a message.
    
    This tool requires OAuth authentication. It adds an emoji reaction to a message.
    
    Args:
        message_name: The resource name of the message (spaces/*/messages/*)
        emoji: The emoji to add as a reaction (e.g. '👍', '❤️', etc.)
        
    Returns:
        Response with information about the added reaction
    """
    from google_chat import add_emoji_reaction
    return await add_emoji_reaction(message_name, emoji)

@mcp.tool()
async def upload_attachment(space_name: str, file_path: str, message_text: str = None) -> Dict:
    """Upload a file attachment to a Google Chat space.
    
    This tool requires OAuth authentication. It uploads a file as an attachment
    to a message in a Google Chat space.
    
    Args:
        space_name: The name/identifier of the space to send the attachment to
        file_path: Path to the file to upload (must be accessible to the server)
        message_text: Optional text message to accompany the attachment
        
    Returns:
        The created message object with the attachment
    """
    from google_chat import upload_attachment
    return await upload_attachment(space_name, file_path, message_text)

@mcp.tool()
async def batch_send_messages(messages: List[Dict]) -> Dict:
    """Send multiple messages in batch to different spaces.
    
    This tool requires OAuth authentication. It sends multiple messages to
    different spaces in one operation.
    
    Args:
        messages: List of message objects, each containing:
            - space_name: The name/identifier of the space to send to
            - text: Text content of the message
            - thread_key: Optional thread key to reply to
            - cards_v2: Optional card content
            
    Returns:
        Dictionary with results for each message, showing which were successful and which failed
    """
    from google_chat import batch_send_messages
    return await batch_send_messages(messages)

@mcp.tool()
async def send_file_message(space_name: str, file_path: str, message_text: str = None) -> Dict:
    """Send a message with file contents as a workaround for attachments.
    
    This tool requires OAuth authentication. Instead of using true file attachments, 
    this tool reads the file and includes its text content in the message body.
    
    Args:
        space_name: The name/identifier of the space to send the file content to
        file_path: Path to the file whose contents will be included in the message
        message_text: Optional text message to accompany the file contents
        
    Returns:
        The created message object
    """
    from google_chat import send_file_message
    return await send_file_message(space_name, file_path, message_text)

@mcp.tool()
async def send_file_content(space_name: str, file_path: str = None) -> Dict:
    """Send file content as a message (workaround for attachments).
    
    This tool requires OAuth authentication. Instead of true attachments,
    this sends the file content as a formatted message.
    
    Args:
        space_name: The space to send the message to
        file_path: Optional path to the file to send. If not provided, will use sample_attachment.txt
        
    Returns:
        The created message object
    """
    from google_chat import create_message
    import os
    
    # Default to sample_attachment.txt if no file specified
    if not file_path:
        file_path = "sample_attachment.txt"
        
    # Create sample file if it doesn't exist
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            f.write("This is a sample attachment file created for testing the Google Chat MCP tools.\n")
            f.write("Line 2: This demonstrates our workaround for file sharing.\n")
            f.write("Line 3: The actual attachment upload API needs more work.\n")
            
    # Read file contents
    try:
        with open(file_path, 'r') as f:
            file_contents = f.read(4000)  # Limit to 4000 chars
    except:
        file_contents = "[Error reading file]"
    
    # Format the message
    message = f"📄 **File Content: {os.path.basename(file_path)}**\n\n```\n{file_contents}\n```"
    
    if not space_name.startswith('spaces/'):
        space_name = f"spaces/{space_name}"
        
    return await create_message(space_name, message)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='MCP Server with Google Chat Authentication')
    parser.add_argument('-local-auth', action='store_true', help='Run the local authentication server')
    parser.add_argument('--host', default='localhost', help='Host to bind the server to (default: localhost)')
    parser.add_argument('--port', type=int, default=8000, help='Port to run the server on (default: 8000)')
    parser.add_argument('--token-path', default='token.json', help='Path to store OAuth token (default: token.json)')
    
    args = parser.parse_args()
    
    # Set the token path for OAuth storage
    set_token_path(args.token_path)
    
    if args.local_auth:
        print(f"\nStarting local authentication server at http://{args.host}:{args.port}")
        print("Available endpoints:")
        print("  - /auth   : Start OAuth authentication flow")
        print("  - /status : Check authentication status")
        print("  - /auth/callback : OAuth callback endpoint")
        print(f"\nDefault callback URL: {DEFAULT_CALLBACK_URL}")
        print(f"Token will be stored at: {args.token_path}")
        print("\nPress CTRL+C to stop the server")
        print("-" * 50)
        run_auth_server(port=args.port, host=args.host)
    else:
        mcp.run()