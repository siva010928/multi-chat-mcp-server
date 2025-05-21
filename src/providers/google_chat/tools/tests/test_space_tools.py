#!/usr/bin/env python3

"""
Test module for Google Chat MCP space-related tools.
"""
import pytest
from datetime import datetime
from src.providers.google_chat.tools.space_tools import (
    get_chat_spaces_tool,
    get_conversation_participants_tool,
    manage_space_members_tool,
    summarize_conversation_tool,
)


@pytest.mark.asyncio
class TestGoogleChatSpaceTools:

    async def test_get_chat_spaces_tool(self, authenticated):
        """Ensure chat spaces can be listed."""
        spaces = await get_chat_spaces_tool()
        assert isinstance(spaces, list)
        assert len(spaces) > 0
        assert "name" in spaces[0]
        assert spaces[0]["name"].startswith("spaces/")

    async def test_get_conversation_participants_tool(self, authenticated, test_space):
        """Ensure participant info is returned from a space."""
        result = await get_conversation_participants_tool(test_space)
        assert isinstance(result, list)
        if result:
            assert "display_name" in result[0] or "email" in result[0]

    async def test_get_conversation_participants_date_filter(self, authenticated, test_space):
        """Ensure date range filtering works in participant analysis."""
        result = await get_conversation_participants_tool(
            test_space,
            start_date="2025-01-01",
            end_date=datetime.now().strftime('%Y-%m-%d')
        )
        assert isinstance(result, list)

    async def test_get_conversation_participants_invalid_dates(self, test_space):
        """Ensure date format errors are handled."""
        with pytest.raises(ValueError, match="start_date must be in YYYY-MM-DD"):
            await get_conversation_participants_tool(test_space, start_date="01-01-2025")

        with pytest.raises(ValueError, match="start_date must be before end_date"):
            await get_conversation_participants_tool(test_space, start_date="2025-05-20", end_date="2025-01-01")

    async def test_manage_space_members_invalid_user(self, authenticated, test_space):
        """Ensure member add operation with invalid email fails gracefully."""
        result = await manage_space_members_tool(
            space_name=test_space,
            operation="add",
            user_emails=["nonexistent-user@example.com"]
        )
        assert isinstance(result, dict)
        assert "failed" in result or "error" in str(result).lower()

    async def test_manage_space_members_invalid_operation(self, test_space):
        """Ensure invalid operations are rejected."""
        with pytest.raises(Exception):
            await manage_space_members_tool(space_name=test_space, operation="invalid", user_emails=[])

    async def test_summarize_conversation_tool(self, authenticated, test_space):
        """Ensure conversation summary includes all major fields."""
        result = await summarize_conversation_tool(
            space_name=test_space,
            message_limit=5
        )
        assert "space" in result
        assert "participants" in result
        assert "messages" in result
        assert isinstance(result["messages"], list)

    async def test_summarize_conversation_tool_date_range(self, authenticated, test_space):
        """Ensure summarization with date range works."""
        result = await summarize_conversation_tool(
            space_name=test_space,
            message_limit=5,
            start_date="2025-01-01",
            end_date=datetime.now().strftime('%Y-%m-%d')
        )
        assert "space" in result
        assert "participants" in result
        assert isinstance(result["participants"], list)

    async def test_summarize_conversation_invalid_dates(self, test_space):
        """Ensure summarization fails with bad dates."""
        with pytest.raises(ValueError, match="start_date must be in YYYY-MM-DD"):
            await summarize_conversation_tool(test_space, start_date="01/01/2025")

        with pytest.raises(ValueError, match="start_date must be before end_date"):
            await summarize_conversation_tool(
                test_space, start_date="2025-05-20", end_date="2025-01-01"
            )
