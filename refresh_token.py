#!/usr/bin/env python
"""
Token Refresh Utility for Google Chat MCP Server

This script provides a simple way to refresh the OAuth token used by the 
Google Chat MCP Server without having to start the full authentication server.

Usage:
  python refresh_token.py [--token-path path/to/token.json]

Options:
  --token-path PATH  Path to the token file (default: token.json)
"""

import asyncio
import argparse
from pathlib import Path
from google_chat import refresh_token, set_token_path, get_credentials
from datetime import timezone


async def main(token_path):
    """Main function to refresh the token"""
    print(f"Attempting to refresh token at: {token_path}")
    
    # Set the token path if specified
    if token_path != "token.json":
        set_token_path(token_path)
    
    # Try to refresh the token
    success, message = await refresh_token(token_path)
    
    if success:
        print(f"✅ Success: {message}")
        # Get and display token info
        creds = get_credentials(token_path)
        if creds and creds.expiry:
            # Ensure we have a timezone-aware datetime
            if creds.expiry.tzinfo is None:
                expiry = creds.expiry.replace(tzinfo=timezone.utc)
            else:
                expiry = creds.expiry
                
            print(f"Token valid until: {expiry.isoformat()}")
        print(f"Refresh token available: {'Yes' if creds and creds.refresh_token else 'No'}")
    else:
        print(f"❌ Failed: {message}")
        print("\nTroubleshooting:")
        print("  1. Check if the token file exists")
        print("  2. If the token is invalid, try re-authenticating:")
        print("     python server.py -local-auth")
        print("     Then visit http://localhost:8000/auth in your browser")


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Refresh the Google Chat OAuth token")
    parser.add_argument("--token-path", default="token.json", 
                      help="Path to the token file (default: token.json)")
    
    args = parser.parse_args()
    
    # Check if token file exists
    token_file = Path(args.token_path)
    if not token_file.exists():
        print(f"❌ Error: Token file not found at {token_file}")
        print("Please authenticate first by running:")
        print("  python server.py -local-auth")
        print("  Then visit http://localhost:8000/auth in your browser")
        exit(1)
    
    # Run the async main function
    asyncio.run(main(args.token_path)) 