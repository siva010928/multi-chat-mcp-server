# Token Management Guide for Google Chat MCP Server

This document provides a comprehensive guide to managing authentication tokens for the Google Chat MCP Server.

## Understanding OAuth 2.0 Authentication

The Google Chat MCP Server uses OAuth 2.0 to authenticate with Google's APIs. This authentication flow involves:

1. **Access Token**: A short-lived token (typically valid for 1 hour) that allows the server to make API calls
2. **Refresh Token**: A long-lived token that allows the server to obtain new access tokens without requiring user re-authentication
3. **Token File**: A JSON file (default: `token.json`) that stores both tokens and related information

## Automatic Token Management

Under normal circumstances, you don't need to manually manage tokens. The server will:

1. Check if the access token is expired before making any API call
2. If expired, automatically use the refresh token to obtain a new access token
3. Save the updated tokens back to the token file
4. Continue with the API call

## Monitoring Token Status

You can check the status of your tokens at any time using the `check_token.py` utility:

```bash
python check_token.py
```

This will show:
- Whether the token is valid
- When the access token expires
- If a refresh token is available
- Which permissions (scopes) have been granted

## Manual Token Refresh

If needed, you can manually refresh the access token using the `refresh_token.py` utility:

```bash
python refresh_token.py
```

This will:
1. Use the refresh token to obtain a new access token
2. Save the updated tokens to the token file
3. Display information about the new token

## Custom Token Path

Both utilities support using a custom path for the token file:

```bash
python check_token.py --token-path /path/to/custom/token.json
python refresh_token.py --token-path /path/to/custom/token.json
```

When starting the server, you can also specify a custom token path:

```bash
python server.py --token-path /path/to/custom/token.json
```

## Complete Re-authentication

There are times when you need to completely re-authenticate:

1. When you've modified the `SCOPES` in the code (changed permissions)
2. If your refresh token has expired (after 6+ months of inactivity)
3. If you want to authenticate with a different Google account

To re-authenticate:

1. Delete the token file:
   ```bash
   rm token.json
   ```

2. Start the authentication server:
   ```bash
   python server.py -local-auth
   ```

3. Visit http://localhost:8000/auth in your browser
   
4. Follow the Google authentication prompts
   
5. Once complete, the token file will be created and ready to use

## Authentication Server

The authentication server provides additional endpoints for token management:

- **http://localhost:8000/auth**: Start the authentication flow
- **http://localhost:8000/status**: Check token status
- **http://localhost:8000/auth/refresh**: Manually refresh the token

To start the authentication server:

```bash
python server.py -local-auth
```

## Required OAuth Scopes

The server requires these OAuth scopes to function properly:

```python
SCOPES = [
    'https://www.googleapis.com/auth/chat.spaces.readonly',
    'https://www.googleapis.com/auth/chat.messages',
    'https://www.googleapis.com/auth/chat.messages.create',
    'https://www.googleapis.com/auth/chat.spaces',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/userinfo.email',
    'openid'
]
```

If you modify these scopes, you must delete the token file and re-authenticate.

## Troubleshooting

### "Invalid Credentials" Error

If you see "Invalid Credentials" errors:

1. Check token status: `python check_token.py`
2. Try refreshing the token: `python refresh_token.py`
3. If that doesn't work, re-authenticate completely

### "Permission Denied" Error

If you see "Permission Denied" errors:

1. Check if the required scope is in the `SCOPES` list in `google_chat.py`
2. If you've added a new scope, delete the token file and re-authenticate
3. Verify the scope was actually granted during authentication by checking with `check_token.py`

### Missing Refresh Token

If refresh tokens aren't being issued:

1. Ensure you're using `access_type='offline'` and `prompt='consent'` in the auth flow
2. Delete any existing token files and re-authenticate
3. Make sure you complete the consent screen during authentication

### Token Format and Storage

The token file is a JSON file containing:

- `token`: The access token
- `refresh_token`: The refresh token
- `token_uri`: The URI for refreshing tokens
- `client_id`: Your OAuth client ID
- `client_secret`: Your OAuth client secret
- `scopes`: The permissions granted
- `expiry`: When the access token expires

Never share your token file as it contains sensitive credentials. 