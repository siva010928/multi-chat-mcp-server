import argparse
import asyncio
import logging

from server_auth import run_auth_server
from src.google_chat.auth import set_token_path
from src.google_chat.constants import DEFAULT_CALLBACK_URL
from src.mcp_instance import mcp

# Import tool modules - this ensures the decorated functions are registered

# Configure logging for better debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main function to run the server, can be called directly or from an external script"""
    parser = argparse.ArgumentParser(description='MCP Server with Google Chat Authentication')
    parser.add_argument('-local-auth', action='store_true', help='Run the local authentication server')
    parser.add_argument('--host', default='localhost', help='Host to bind the server to (default: localhost)')
    parser.add_argument('--port', type=int, default=8000, help='Port to run the server on (default: 8000)')
    parser.add_argument('--token-path', default='token.json', help='Path to store OAuth token (default: token.json)')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')

    args = parser.parse_args()

    # Set debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger("fastmcp").setLevel(logging.DEBUG)
    
    # Set the token path for OAuth storage
    set_token_path(args.token_path)

    if args.local_auth:
        print(f"\nStarting local authentication server at http://{args.host}:{args.port}")
        print("Available endpoints:")
        print("  - /auth   : Start OAuth authentication flow")
        print("  - /status : Check authentication status")
        print("  - /auth/callback : OAuth callback endpoint")
        print(f"\nDefault callback URL: {DEFAULT_CALLBACK_URL}")
        print(f"Token will be stored at: {args.token_path}")
        print("\nPress CTRL+C to stop the server")
        print("-" * 50)
        run_auth_server(port=args.port, host=args.host)
    else:
        # Debug info
        logger.info("Initializing Google Chat MCP Server...")
        
        # Get and print registered tools
        tools = asyncio.run(mcp.get_tools())
        
        if tools:
            logger.info(f"Successfully registered {len(tools)} tools:")
            for name, tool in tools.items():
                logger.info(f"- {name}")
        else:
            logger.warning("No tools were registered!")
        
        # Run the MCP server
        logger.info("Starting MCP server...")
        mcp.run()

if __name__ == "__main__":
    main()