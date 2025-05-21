import asyncio
import os
import signal
from pathlib import Path
from typing import Optional, Dict

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse, RedirectResponse
from google_auth_oauthlib.flow import InstalledAppFlow

from src.providers.google_chat.api.auth import get_credentials, token_info, save_credentials, refresh_token
from src.providers.google_chat.utils.constants import DEFAULT_CALLBACK_URL, SCOPES, CREDENTIALS_FILE

# Store OAuth flow state
oauth_flows: Dict[str, InstalledAppFlow] = {}

# Create FastAPI app for local auth server
app = FastAPI(title="Google Chat Auth Server")

@app.get("/auth")
async def start_auth(callback_url: Optional[str] = Query(None)):
    """Start OAuth authentication flow"""
    try:
        # Check if we already have valid credentials
        if get_credentials():
            return JSONResponse(
                content={
                    "status": "already_authenticated",
                    "message": "Valid credentials already exist"
                }
            )

        # Initialize OAuth 2.0 flow
        if not os.path.exists(CREDENTIALS_FILE):
            raise FileNotFoundError(
                f"credentials.json not found in {CREDENTIALS_FILE}. Please download it from Google Cloud Console "
                "and save it in the current directory."
            )

        flow = InstalledAppFlow.from_client_secrets_file(
            str(CREDENTIALS_FILE), 
            SCOPES,
            redirect_uri=callback_url or DEFAULT_CALLBACK_URL
        )

        # Generate authorization URL with offline access and force approval
        auth_url, state = flow.authorization_url(
            access_type='offline',  # Enable offline access
            prompt='consent',       # Force consent screen to ensure refresh token
            include_granted_scopes='true'
        )

        # Store the flow object for later use
        oauth_flows[state] = flow

        # Redirect user to Google's auth page
        return RedirectResponse(url=auth_url)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/auth/callback")
async def auth_callback(
    state: str = Query(...),
    code: Optional[str] = Query(None),
    error: Optional[str] = Query(None)
):
    """Handle OAuth callback"""
    try:
        if error:
            raise HTTPException(
                status_code=400,
                detail=f"Authorization failed: {error}"
            )

        if not code:
            raise HTTPException(
                status_code=400,
                detail="No authorization code received"
            )

        # Retrieve the flow object
        flow = oauth_flows.get(state)
        if not flow:
            raise HTTPException(
                status_code=400,
                detail="Invalid state parameter"
            )

        try:
            # Exchange auth code for credentials with offline access
            print("fetching token: ", code)
            flow.fetch_token(
                code=code,
                # Ensure we're requesting offline access for refresh tokens
                access_type='offline'
            )
            print("fetched credentials: ", flow.credentials)
            creds = flow.credentials

            # Verify we got a refresh token
            if not creds.refresh_token:
                raise HTTPException(
                    status_code=400,
                    detail="Failed to obtain refresh token. Please try again."
                )

            # Save credentials both to file and memory
            print("saving credentials: ", creds)
            save_credentials(creds)

            # Clean up the flow object
            del oauth_flows[state]

            return JSONResponse(
                content={
                    "status": "success",
                    "message": "Authorization successful. Long-lived token obtained. You can close this window.",
                    "token_file": token_info['token_path'],
                    "expires_at": creds.expiry.isoformat() if creds.expiry else None,
                    "has_refresh_token": bool(creds.refresh_token)
                }
            )
        except Exception as e:
            # Clean up flow object even if there's an error
            del oauth_flows[state]
            raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/refresh")
async def manual_token_refresh():
    """Manually trigger a token refresh"""
    success, message = await refresh_token()
    if success:
        creds = token_info['credentials']
        return JSONResponse(
            content={
                "status": "success",
                "message": message,
                "expires_at": creds.expiry.isoformat() if creds.expiry else None,
                "last_refresh": token_info['last_refresh'].isoformat()
            }
        )
    else:
        raise HTTPException(
            status_code=400,
            detail=message
        )

@app.get("/status")
async def check_auth_status():
    """Check if we have valid credentials"""
    token_path = token_info['token_path']
    token_file = Path(token_path)
    if not token_file.exists():
        return JSONResponse(
            content={
                "status": "not_authenticated",
                "message": "No authentication token found",
                "token_path": str(token_path)
            }
        )
    
    try:
        creds = get_credentials()
        if creds:
            return JSONResponse(
                content={
                    "status": "authenticated",
                    "message": "Valid credentials exist",
                    "token_path": str(token_path),
                    "expires_at": creds.expiry.isoformat() if creds.expiry else None,
                    "last_refresh": token_info['last_refresh'].isoformat() if token_info['last_refresh'] else None,
                    "has_refresh_token": bool(creds.refresh_token)
                }
            )
        else:
            return JSONResponse(
                content={
                    "status": "expired",
                    "message": "Credentials exist but are expired or invalid",
                    "token_path": str(token_path)
                }
            )
    except Exception as e:
        return JSONResponse(
            content={
                "status": "error",
                "message": str(e),
                "token_path": str(token_path)
            },
            status_code=500
        )

def run_auth_server(port: int = 8000, host: str = "localhost"):
    """Run the authentication server with graceful shutdown support
    
    Args:
        port: Port to run the server on (default: 8000)
        host: Host to bind the server to (default: localhost)
    """
    server_config = uvicorn.Config(app, host=host, port=port)
    server = uvicorn.Server(server_config)
    
    # Handle graceful shutdown
    def signal_handler(signum, frame):
        print("\nReceived signal to terminate. Performing graceful shutdown...")
        asyncio.create_task(server.shutdown())
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)  # Handle Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Handle termination signal
    
    try:
        print(f"\nServer is running at: http://{host}:{port}")
        print(f"Default callback URL: {DEFAULT_CALLBACK_URL}")
        # Start the server
        server.run()
    except KeyboardInterrupt:
        print("\nShutting down the auth server...")
    finally:
        print("Auth server has been stopped.") 