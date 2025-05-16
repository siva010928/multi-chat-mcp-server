from typing import List, Dict, Optional
from googleapiclient.discovery import build

from auth import get_credentials


async def create_interactive_card_message(space_name: str,
                                          card_title: str,
                                          card_subtitle: str = None,
                                          card_image_url: str = None,
                                          sections: List[Dict] = None,
                                          buttons: List[Dict] = None) -> Dict:
    """Creates a message with an interactive card in a Google Chat space.

    Args:
        space_name: The name/identifier of the space to send the message to
        card_title: Title for the card
        card_subtitle: Optional subtitle for the card
        card_image_url: Optional image URL to display in the card header
        sections: Optional list of sections for the card, each section is a dict with:
            - header: Optional header text for the section
            - widgets: List of widgets in the section
        buttons: Optional list of buttons to add to the card, each button is a dict with:
            - text: Button text
            - onClick: Action to perform when clicked (e.g. openLink or action)

    Returns:
        The created message object

    Raises:
        Exception: If authentication fails or message creation fails
    """
    try:
        creds = get_credentials()
        if not creds:
            raise Exception("No valid credentials found. Please authenticate first.")

        service = build('chat', 'v1', credentials=creds)

        # Build card header
        card_header = {"title": card_title}
        if card_subtitle:
            card_header["subtitle"] = card_subtitle
        if card_image_url:
            card_header["imageUrl"] = card_image_url
            card_header["imageType"] = "SQUARE"  # Default to SQUARE, can be CIRCLE or RECTANGLE

        # Build card sections
        card_sections = []

        if sections:
            card_sections.extend(sections)

        # Add buttons as a separate section with buttonList widget if provided
        if buttons:
            button_section = {
                "widgets": [{
                    "buttonList": {
                        "buttons": buttons
                    }
                }]
            }
            card_sections.append(button_section)

        # Build the complete card
        card = {
            "card": {
                "header": card_header,
                "sections": card_sections
            }
        }

        # Build message body (no text, just the card)
        message_body = {"cardsV2": [card]}

        # Make API request
        response = service.spaces().messages().create(
            parent=space_name,
            body=message_body
        ).execute()

        return response

    except Exception as e:
        raise Exception(f"Failed to create interactive card message: {str(e)}")
