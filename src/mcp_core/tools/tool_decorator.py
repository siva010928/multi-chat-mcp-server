"""
Tool decorator module for MCP.

This module provides a wrapper for the FastMCP tool decorator that also registers
the tool with the central registry.
"""

import logging
from typing import Callable, Any

from src.mcp_core.tools.registry import register_tool

# Set up logger
logger = logging.getLogger(__name__)

def register_with_registry(provider_name: str, tool_name: str, fn: Callable) -> None:
    """
    Register a tool with the central registry.
    
    Args:
        provider_name: The name of the provider.
        tool_name: The name of the tool.
        fn: The function implementing the tool.
    """
    # Register the tool with the central registry
    registry_name = f"{provider_name}.{tool_name}"
    register_tool(registry_name, fn)
    logger.debug(f"Registered tool '{tool_name}' from provider '{provider_name}' with central registry as '{registry_name}'")

def tool_decorator_factory(provider_name: str, mcp_instance: Any) -> Callable:
    """
    Create a tool decorator that registers tools with both the MCP instance and the central registry.
    
    Args:
        provider_name: The name of the provider.
        mcp_instance: The MCP instance to register tools with.
        
    Returns:
        A decorator function that registers tools with both the MCP instance and the central registry.
    """
    def tool_decorator(*args, **kwargs) -> Callable:
        """
        Decorator that registers a function as a tool with both the MCP instance and the central registry.
        
        This decorator wraps the FastMCP tool decorator and adds registration with the central registry.
        
        Args:
            *args: Arguments to pass to the FastMCP tool decorator.
            **kwargs: Keyword arguments to pass to the FastMCP tool decorator.
            
        Returns:
            A decorator function that registers the decorated function as a tool.
        """
        # Get the original FastMCP tool decorator
        original_decorator = mcp_instance.tool(*args, **kwargs)
        
        def wrapper(fn: Callable) -> Callable:
            # Register the tool with the FastMCP instance
            decorated_fn = original_decorator(fn)
            
            # Register the tool with the central registry
            tool_name = fn.__name__
            register_with_registry(provider_name, tool_name, fn)
            
            return decorated_fn
        
        return wrapper
    
    return tool_decorator