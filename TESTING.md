# Testing Guide for Google Chat MCP Server

This document provides an overview of the testing setup and coverage for the Google Chat MCP Server.

## Testing Framework

The project uses pytest as its primary testing framework with the following extensions:

- **pytest-cov**: For coverage reporting
- **pytest-asyncio**: For testing asynchronous functions

## Test Files

The test suite is organized into several test files:

1. **test_auth.py**: Tests for authentication functions
   - Tests token path setting
   - Tests loading and saving credentials
   - Tests token refresh functionality

2. **test_token_management.py**: Tests for token management utilities
   - Tests token expiry calculation
   - Tests automatic token refresh
   - Tests for both synchronous and asynchronous functions

3. **test_messaging.py**: Tests for message operations
   - Tests sending messages to spaces
   - Tests updating messages
   - Tests creating interactive cards
   - Tests message threading

4. **test_search_batch.py**: Tests for search and batch operations
   - Tests message search functionality
   - Tests batch message sending

5. **test_file_operations.py**: Tests for file-related functions
   - Tests sending file content as messages
   - Tests file uploads

6. **test_user_info.py**: Tests for user info and mentions
   - Tests retrieving user profile information
   - Tests finding mentions of usernames in messages

## Asynchronous Testing

The project uses `pytest-asyncio` to test asynchronous functions. Asynchronous tests are marked with the `@pytest.mark.asyncio` decorator.

Example:
```python
@pytest.mark.asyncio
async def test_refresh_token_coroutine():
    # Test async function
    result = await google_chat.refresh_token()
    assert result is not None
```

## Current Coverage

As of the latest update, the test suite achieves **63%** code coverage for the `google_chat.py` module. This covers the core functionality of the library, including:

- Authentication and token management
- Message sending and reading
- User information retrieval
- Space management
- Search functionality

Areas with lower coverage include some edge cases and error handling paths that are challenging to test without actually connecting to the Google Chat API.

## Running Tests

To run the full test suite:

```bash
python -m pytest
```

To run tests with coverage reporting:

```bash
python -m pytest --cov=google_chat
```

To run a specific test file:

```bash
python -m pytest tests/test_auth.py
```

## Token Management Testing

Token management has comprehensive tests covering:

1. **Token Path Configuration**: Tests for setting and retrieving token paths
2. **Token Loading**: Tests for loading token from file
3. **Token Auto-refresh**: Tests for automatic refreshing of expired tokens
4. **Expiry Calculation**: Tests for calculating token expiry times
5. **Async Token Functions**: Tests for asynchronous token refresh functions

## Writing New Tests

When adding new functionality to the library, please follow these guidelines:

1. Create tests for both happy paths and error cases
2. Mock external API calls using `unittest.mock`
3. For asynchronous functions, use the `@pytest.mark.asyncio` decorator
4. Add appropriate assertions to validate function behavior
5. Maintain test isolation - tests should not depend on each other

## Continuous Integration

Tests are run automatically on every pull request to ensure code quality. 