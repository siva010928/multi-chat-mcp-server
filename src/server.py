import argparse
import asyncio
import logging
import os
import sys
from typing import Dict, Any

# Add the parent directory to the Python path so we can import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.mcp_core.engine.provider_loader import load_provider_config, load_provider_modules, get_available_providers, initialize_provider_config
from src.mcp_core.tools.registry import get_all_tools as get_all_registry_tools

# Configure logging for better debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main function to run the server, can be called directly or from an external script"""
    parser = argparse.ArgumentParser(description='Multi-Provider MCP Server')
    parser.add_argument('--provider', help='Provider to use (e.g., google_chat, slack)')
    parser.add_argument('-local-auth', action='store_true', help='Run the local authentication server')
    parser.add_argument('--host', default='localhost', help='Host to bind the server to (default: localhost)')
    parser.add_argument('--port', type=int, default=8000, help='Port to run the server on (default: 8000)')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--list-providers', action='store_true', help='List available providers')

    args = parser.parse_args()

    # Set debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger("fastmcp").setLevel(logging.DEBUG)

    # List available providers if requested
    if args.list_providers:
        providers = get_available_providers()
        if providers:
            print("Available providers:")
            for provider_name, provider_config in providers.items():
                print(f"  - {provider_name}: {provider_config.get('description', 'No description')}")
        else:
            print("No providers found in configuration.")
        return

    # Check if provider is specified
    if not args.provider:
        logger.error("No provider specified. Use --provider to specify a provider or --list-providers to see available providers.")
        parser.print_help()
        sys.exit(1)

    # Initialize and load provider configuration
    try:
        # Initialize the configuration for the provider
        # This ensures the configuration is loaded and cached before it's needed by other components
        provider_config = initialize_provider_config(args.provider)
        logger.info(f"Initialized configuration for provider: {args.provider}")
    except ValueError as e:
        logger.error(f"Error initializing provider configuration: {str(e)}")
        sys.exit(1)

    # Load provider modules
    try:
        mcp_instance_module, server_auth_module, _ = load_provider_modules(args.provider)
        logger.info(f"Loaded modules for provider: {args.provider}")
    except ImportError as e:
        logger.error(f"Error loading provider modules: {str(e)}")
        sys.exit(1)

    # Get the MCP instance
    mcp = mcp_instance_module.mcp

    # Handle token path for providers that need it
    if 'token_path' in provider_config:
        token_path = provider_config['token_path']
        # Convert to absolute path if it's a relative path
        if not os.path.isabs(token_path):
            # Get the project root directory (parent of src)
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            token_path = os.path.abspath(os.path.join(project_root, token_path))
        logger.info(f"Using token path: {token_path}")

        # Set token path in auth module if it has the set_token_path function
        if hasattr(server_auth_module, 'set_token_path'):
            logger.info(f"Setting token path in server_auth_module: {token_path}")
            server_auth_module.set_token_path(token_path)

        # Import and set token path in auth module directly
        try:
            from src.providers.google_chat.api.auth import set_token_path
            logger.info(f"Setting token path in auth module: {token_path}")
            set_token_path(token_path)
        except ImportError:
            logger.warning(f"Could not import set_token_path from auth module")

        # Ensure the token file exists
        if not os.path.exists(token_path):
            logger.warning(f"Token file does not exist: {token_path}")
            if args.local_auth:
                logger.info(f"Will create token file during authentication")
            else:
                logger.error(f"Token file not found. Please run with -local-auth to authenticate first.")
                print(f"\nToken file not found: {token_path}")
                print("Please run with -local-auth to authenticate first:")
                print(f"  python -m src.server --provider {args.provider} -local-auth")
                sys.exit(1)

    if args.local_auth:
        port = provider_config.get('port', args.port)
        callback_url = provider_config.get('callback_url', f"http://{args.host}:{port}/auth/callback")

        print(f"\nStarting local authentication server for {args.provider} at http://{args.host}:{port}")
        print("Available endpoints:")
        print("  - /auth   : Start OAuth authentication flow")
        print("  - /status : Check authentication status")
        print("  - /auth/callback : OAuth callback endpoint")
        print(f"\nCallback URL: {callback_url}")
        print(f"Token will be stored at: {provider_config.get('token_path', 'default location')}")
        print("\nPress CTRL+C to stop the server")
        print("-" * 50)

        server_auth_module.run_auth_server(port=port, host=args.host)
    else:
        # Debug info
        logger.info(f"Initializing {mcp.name}...")

        # Get and print registered tools from MCP instance
        mcp_tools = asyncio.run(mcp.get_tools())

        # Get tools from central registry
        registry_tools = get_all_registry_tools()

        if mcp_tools:
            logger.info(f"Successfully registered {len(mcp_tools)} tools with MCP instance:")
            for name, tool in mcp_tools.items():
                logger.info(f"- {name}")
        else:
            logger.warning("No tools were registered with MCP instance!")

        if registry_tools:
            logger.info(f"Successfully registered {len(registry_tools)} tools with central registry:")
            for name, tool in registry_tools.items():
                logger.info(f"- {name}")
        else:
            logger.warning("No tools were registered with central registry!")

        # Run the MCP server
        logger.info(f"Starting {mcp.name}...")
        mcp.run()

if __name__ == "__main__":
    main()
