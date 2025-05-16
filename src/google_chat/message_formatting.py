"""
Message formatting utilities for Google Chat API.
Includes helpers for text, markdown, code, emoji, and card content.
"""

import re

def format_bold(text: str) -> str:
    """Format text as bold for Google Chat markdown."""
    return f"*{text}*"

def format_italic(text: str) -> str:
    """Format text as italic for Google Chat markdown."""
    return f"_{text}_"

def format_strikethrough(text: str) -> str:
    """Format text as strikethrough for Google Chat markdown."""
    return f"~{text}~"

def format_code(text: str) -> str:
    """Format text as inline code for Google Chat markdown."""
    return f"`{text}`"

def format_code_block(text: str, language: str = "") -> str:
    """Format text as a code block."""
    if language:
        return f"```{language}\n{text}\n```"
    return f"```\n{text}\n```"

def add_emoji(text: str, emoji: str) -> str:
    """Append an emoji to text (as Unicode or short name)."""
    return f"{text} {emoji}"

def sanitize_message(text: str) -> str:
    """Basic sanitation to avoid breaking markdown."""
    if not text:
        return ""
    # Remove dangerous markdown characters
    return re.sub(r'([*_~`])', r'\\\1', text)

def format_user_mention(email: str) -> str:
    """Format a user mention by email for Google Chat (note: true mentions use userId)."""
    return f"@{email}"

def truncate_message(text: str, max_length: int = 4000) -> str:
    """Truncate message safely for Chat API limits."""
    if len(text) > max_length:
        return text[:max_length-3] + "..."
    return text

def format_list(items, bullet: str = "-") -> str:
    """Format a list of strings as a markdown bullet list."""
    return "\n".join(f"{bullet} {item}" for item in items)

def format_table(rows, header=None) -> str:
    """Format a table as markdown (simple)."""
    lines = []
    if header:
        lines.append(" | ".join(header))
        lines.append("-|-".join('-' * len(col) for col in header))
    for row in rows:
        lines.append(" | ".join(str(cell) for cell in row))
    return "\n".join(lines)

# Add more as needed for your bot/app!
