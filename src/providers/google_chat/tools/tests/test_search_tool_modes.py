from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from src.providers.google_chat.tools.search_tools import search_messages_tool

SPACE_ID = "spaces/abc"

# Shared fixtures
MOCK_MESSAGES_REGEX = [
    {"name": "spaces/abc/messages/1", "text": "Release v1.2.3 deployed to staging", "createTime": "2024-05-15T10:00:00Z"},
    {"name": "spaces/abc/messages/2", "text": "Reminder: Team meeting at 4PM", "createTime": "2024-05-15T11:00:00Z"},
    {"name": "spaces/abc/messages/3", "text": "Patch deployed as v2.0.1-beta", "createTime": "2024-05-18T14:22:00Z"},
    {"name": "spaces/abc/messages/4", "text": "Production deploy failed [ERROR]", "createTime": "2024-05-19T16:45:00Z"},
]

MOCK_MESSAGES_SEMANTIC = [
    {"name": "msg1", "text": "API response times are down by 40%"},
    {"name": "msg2", "text": "Intermittent latency after database migration"},
    {"name": "msg3", "text": "Q3 roadmap includes billing and IAM updates"},
    {"name": "msg4", "text": "Issue with invoices for multi-org accounts"},
    {"name": "msg5", "text": "Engineering all-hands tomorrow 2PM"},
    {"name": "msg6", "text": "Sprint retro covered LaunchDarkly migration"},
]

@pytest.mark.asyncio
class TestRegexSearchTool:

    @patch("src.providers.google_chat.api.search.list_space_messages", new_callable=AsyncMock)
    async def test_find_version_tags(self, mock_list):
        mock_list.return_value = {"messages": MOCK_MESSAGES_REGEX}
        result = await search_messages_tool(r"v\d+\.\d+\.\d+(-\w+)?", "regex", [SPACE_ID])
        assert len(result["messages"]) == 2

    @patch("src.providers.google_chat.api.search.list_space_messages", new_callable=AsyncMock)
    async def test_detect_deploy_failures(self, mock_list):
        mock_list.return_value = {"messages": MOCK_MESSAGES_REGEX}
        result = await search_messages_tool(r"deploy.*(fail|error)|fail.*deploy", "regex", [SPACE_ID])
        assert any("fail" in m["text"].lower() or "error" in m["text"].lower() for m in result["messages"])

    @patch("src.providers.google_chat.api.search.list_space_messages", new_callable=AsyncMock)
    async def test_extract_time_mentions(self, mock_list):
        mock_list.return_value = {"messages": MOCK_MESSAGES_REGEX}
        result = await search_messages_tool(r"\b\d{1,2}(:\d{2})?(AM|PM)\b", "regex", [SPACE_ID])
        assert any("4PM" in m["text"] for m in result["messages"])

    @patch("src.providers.google_chat.api.search.list_space_messages", new_callable=AsyncMock)
    async def test_error_log_detection(self, mock_list):
        mock_list.return_value = {"messages": MOCK_MESSAGES_REGEX}
        result = await search_messages_tool(r"\[ERROR\]", "regex", [SPACE_ID])
        assert len(result["messages"]) == 1
        assert "[ERROR]" in result["messages"][0]["text"]

    @patch("src.providers.google_chat.api.search.list_space_messages", new_callable=AsyncMock)
    async def test_date_filtered_regex_search(self, mock_list):
        filtered = [m for m in MOCK_MESSAGES_REGEX if m["createTime"] > "2024-05-17T00:00:00Z"]
        mock_list.return_value = {"messages": filtered}
        result = await search_messages_tool(r"v\d+\.\d+\.\d+", "regex", [SPACE_ID], days_window=7, offset=7)
        assert len(result["messages"]) == 1
        assert "v2.0.1-beta" in result["messages"][0]["text"]


@pytest.mark.asyncio
class TestSemanticSearchTool:

    @patch("src.providers.google_chat.api.search.SearchManager")
    @patch("src.providers.google_chat.api.search.list_space_messages", new_callable=AsyncMock)
    async def test_semantic_health_terms(self, mock_list, mock_mgr_cls):
        messages = [{"text": line} for line in [
            "I'm feeling sick today and need to take some time off.",
            "Health concern update: reported feeling sick.",
            "This is a test message for date filtering with the word unhealthy in it."
        ]]
        mock_list.return_value = {"messages": messages}
        mock_mgr = MagicMock()
        mock_mgr.search.return_value = [(0.9, msg) for msg in messages]
        mock_mgr.get_default_mode.return_value = "semantic"
        mock_mgr_cls.return_value = mock_mgr

        result = await search_messages_tool("unhealthy", "semantic", [SPACE_ID])
        assert any("unhealthy" in m["text"].lower() for m in result["messages"])

    @patch("src.providers.google_chat.api.search.SearchManager")
    @patch("src.providers.google_chat.api.search.list_space_messages", new_callable=AsyncMock)
    async def test_semantic_performance_query(self, mock_list, mock_mgr_cls):
        mock_list.return_value = {"messages": MOCK_MESSAGES_SEMANTIC}
        mock_mgr = MagicMock()
        mock_mgr.search.return_value = [(0.92, MOCK_MESSAGES_SEMANTIC[0])]
        mock_mgr.get_default_mode.return_value = "semantic"
        mock_mgr_cls.return_value = mock_mgr

        result = await search_messages_tool("performance", "semantic", [SPACE_ID])
        assert "response times" in result["messages"][0]["text"]

    @patch("src.providers.google_chat.api.search.SearchManager")
    @patch("src.providers.google_chat.api.search.list_space_messages", new_callable=AsyncMock)
    async def test_semantic_billing_issue(self, mock_list, mock_mgr_cls):
        mock_list.return_value = {"messages": MOCK_MESSAGES_SEMANTIC}
        mock_mgr = MagicMock()
        mock_mgr.search.return_value = [(0.88, MOCK_MESSAGES_SEMANTIC[3])]
        mock_mgr.get_default_mode.return_value = "semantic"
        mock_mgr_cls.return_value = mock_mgr

        result = await search_messages_tool("billing", "semantic", [SPACE_ID])
        assert "invoice" in result["messages"][0]["text"].lower()

    @patch("src.providers.google_chat.api.search.SearchManager")
    @patch("src.providers.google_chat.api.search.list_space_messages", new_callable=AsyncMock)
    async def test_semantic_retro_outcomes(self, mock_list, mock_mgr_cls):
        mock_list.return_value = {"messages": MOCK_MESSAGES_SEMANTIC}
        mock_mgr = MagicMock()
        mock_mgr.search.return_value = [(0.9, MOCK_MESSAGES_SEMANTIC[5])]
        mock_mgr.get_default_mode.return_value = "semantic"
        mock_mgr_cls.return_value = mock_mgr

        result = await search_messages_tool("retro", "semantic", [SPACE_ID])
        assert "retro" in result["messages"][0]["text"].lower()


@pytest.mark.asyncio
class TestExactSearchTool:

    @patch("src.providers.google_chat.api.search.list_space_messages", new_callable=AsyncMock)
    async def test_exact_phrases(self, mock_list):
        phrases = [
            "CI/CD Pipeline Update Summary",
            "Test message created by diagnostic script",
            "Batch message 1 - Testing batch messaging"
        ]
        mock_list.return_value = {"messages": [{"text": text} for text in phrases]}
        for phrase in phrases:
            result = await search_messages_tool(phrase, "exact", [SPACE_ID])
            assert any(phrase == m["text"] for m in result["messages"])
