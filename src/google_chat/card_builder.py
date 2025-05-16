"""
Helper functions for building Google Chat card payloads.
Supports simple and interactive cards, including sections, images, and buttons.
"""

from typing import List, Dict, Optional

def simple_card(
    title: str,
    description: Optional[str] = None,
    image_url: Optional[str] = None,
    buttons: Optional[List[Dict]] = None,
) -> Dict:
    """
    Create a simple card with a title, optional description, image, and buttons.
    Args:
        title: Title of the card.
        description: Text below the title.
        image_url: Optional image in the card header.
        buttons: List of button dicts from `card_button()`.
    Returns:
        Card payload as a dictionary for Google Chat.
    """
    card = {
        "card": {
            "header": {
                "title": title
            }
        }
    }
    if description:
        card["card"].setdefault("sections", []).append({
            "widgets": [
                {
                    "textParagraph": {"text": description}
                }
            ]
        })
    if image_url:
        card["card"]["header"]["imageUrl"] = image_url

    # Add buttons if present
    if buttons:
        if "sections" not in card["card"]:
            card["card"]["sections"] = []
        card["card"]["sections"].append({
            "widgets": [
                {
                    "buttons": buttons
                }
            ]
        })
    return card

def card_button(
    text: str,
    url: Optional[str] = None,
    action_function: Optional[str] = None,
    action_parameters: Optional[List[Dict]] = None,
) -> Dict:
    """
    Create a button for Google Chat cards.
    Args:
        text: Button label.
        url: URL to open when button is clicked.
        action_function: Name of function to call for interactive workflow.
        action_parameters: List of parameter dicts for the action function.
    Returns:
        Button widget dict.
    """
    btn = {
        "text": text,
        "onClick": {}
    }
    if url:
        btn["onClick"]["openLink"] = {"url": url}
    elif action_function:
        btn["onClick"]["action"] = {
            "function": action_function,
        }
        if action_parameters:
            btn["onClick"]["action"]["parameters"] = action_parameters
    return btn

def interactive_card(
    title: str,
    subtitle: Optional[str] = None,
    image_url: Optional[str] = None,
    sections: Optional[List[Dict]] = None,
    buttons: Optional[List[Dict]] = None,
) -> Dict:
    """
    Build a full-featured interactive card.
    Args:
        title: Card title.
        subtitle: Card subtitle (shown under title).
        image_url: Optional image in the header.
        sections: List of section dicts (with text, fields, etc.).
        buttons: List of button widgets.
    Returns:
        Google Chat card dict.
    """
    header = {"title": title}
    if subtitle:
        header["subtitle"] = subtitle
    if image_url:
        header["imageUrl"] = image_url

    card = {"card": {"header": header}}
    if sections:
        card["card"]["sections"] = sections
    if buttons:
        if "sections" not in card["card"]:
            card["card"]["sections"] = []
        card["card"]["sections"].append({
            "widgets": [
                {"buttons": buttons}
            ]
        })
    return card

def section_text(header: str, text: str) -> Dict:
    """
    Helper for a text section in a card.
    """
    return {
        "header": header,
        "widgets": [
            {"textParagraph": {"text": text}}
        ]
    }

def section_fields(header: str, fields: List[Dict]) -> Dict:
    """
    Helper for a section with multiple labeled key/value fields.
    """
    return {
        "header": header,
        "widgets": [
            {"keyValue": field} for field in fields
        ]
    }

def key_value_field(top_label: str, content: str, icon: Optional[str] = None) -> Dict:
    """
    Create a keyValue widget (labeled field).
    """
    kv = {
        "topLabel": top_label,
        "content": content
    }
    if icon:
        kv["icon"] = icon
    return kv

# More helpers can be added for text inputs, dropdowns, etc. as needed.

