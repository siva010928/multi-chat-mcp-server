#!/usr/bin/env python
"""
Token Status Check Utility for Google Chat MCP Server

This script provides a simple way to check the status of the OAuth token used 
by the Google Chat MCP Server without having to start the full authentication server.

Usage:
  python check_token.py [--token-path path/to/token.json]

Options:
  --token-path PATH  Path to the token file (default: token.json)
"""

import argparse
from pathlib import Path
from google_chat import get_credentials, set_token_path
import datetime
from datetime import timezone


def main(token_path):
    """Check token status and display information"""
    print(f"Checking token at: {token_path}")
    
    # Set the token path if specified
    if token_path != "token.json":
        set_token_path(token_path)
    
    # Get credentials and check status
    creds = get_credentials(token_path)
    
    if not creds:
        print("❌ No valid credentials found")
        print("\nTroubleshooting:")
        print("  1. Check if the token file exists and is valid")
        print("  2. Try refreshing the token: python refresh_token.py")
        print("  3. If needed, re-authenticate: python server.py -local-auth")
        return
    
    # Display token information
    print("✅ Token is valid")
    
    # Show token expiration
    if creds.expiry:
        # Ensure we have a timezone-aware datetime for comparison
        if creds.expiry.tzinfo is None:
            expiry = creds.expiry.replace(tzinfo=timezone.utc)
        else:
            expiry = creds.expiry
            
        now = datetime.datetime.now(timezone.utc)
        time_left = expiry - now
        hours_left = time_left.total_seconds() / 3600
        
        print(f"Token expires at: {expiry.isoformat()}")
        print(f"Time remaining: {hours_left:.1f} hours")
    else:
        print("Token expiration: Unknown")
    
    # Check refresh token
    if creds.refresh_token:
        print("Refresh token: Available ✓")
    else:
        print("Refresh token: Not available ✗")
        print("WARNING: Without a refresh token, the token cannot be automatically renewed")
    
    # Check scopes
    if hasattr(creds, 'scopes'):
        print("\nGRANTED SCOPES:")
        for scope in creds.scopes:
            print(f"  - {scope}")
    
    print("\nIf you need to refresh this token, run:")
    print("  python refresh_token.py")


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Check the Google Chat OAuth token status")
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
    
    # Run the main function
    main(args.token_path) 