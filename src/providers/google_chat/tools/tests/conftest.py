"""
Test fixtures for Google Chat MCP tests.
"""

import pytest
import os
import sys

# Add the project root to the path so we can import the src modules
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))

# Import authentication test instead
from src.providers.google_chat.tools.tests.test_auth_tools import test_authentication
from src.providers.google_chat.api import messages

# Test space for our tests
TEST_SPACE = "spaces/AAQAXL5fJxI"  # Replace with an actual space ID for testing


@pytest.fixture(scope="session")
async def authenticated():
    """Fixture to ensure authentication is working."""
    result = await test_authentication()
    assert result == True, "Authentication failed"
    return result


@pytest.fixture(scope="session")
async def test_space():
    """Fixture to provide a test space."""
    return TEST_SPACE


@pytest.fixture
async def test_message(authenticated, test_space):
    """Create a test message for use in other tests."""
    from datetime import datetime
    test_msg = f"Test message from Google Chat MCP test script - {datetime.now()}"
    try:
        result = await messages.create_message(test_space, test_msg)
        print(f"✅ Created test message: {result.get('name')}")
        return result
    except Exception as e:
        pytest.fail(f"Failed to create test message: {str(e)}")
        return None 