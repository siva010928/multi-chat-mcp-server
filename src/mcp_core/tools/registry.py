"""
Tool registry module for MCP.

This module provides a simple registry for tools that can be used across providers.
"""

import logging
from typing import Dict, Any, Callable, Optional

# Set up logger
logger = logging.getLogger(__name__)

class ToolRegistry:
    """
    A registry for MCP tools.
    
    This class provides methods to register, retrieve, and manage tools.
    """
    
    def __init__(self):
        """Initialize an empty tool registry."""
        self._tools: Dict[str, Callable] = {}
    
    def register_tool(self, name: str, fn: Callable) -> None:
        """
        Register a tool with the registry.
        
        Args:
            name: The name of the tool.
            fn: The function implementing the tool.
            
        Raises:
            ValueError: If a tool with the same name is already registered.
        """
        if name in self._tools:
            logger.warning(f"Tool '{name}' is already registered. Overwriting.")
        
        self._tools[name] = fn
        logger.debug(f"Registered tool: {name}")
    
    def get_tool(self, name: str) -> Optional[Callable]:
        """
        Get a tool by name.
        
        Args:
            name: The name of the tool to retrieve.
            
        Returns:
            The tool function if found, None otherwise.
        """
        return self._tools.get(name)
    
    def get_all_tools(self) -> Dict[str, Callable]:
        """
        Get all registered tools.
        
        Returns:
            A dictionary mapping tool names to their functions.
        """
        return self._tools.copy()
    
    def unregister_tool(self, name: str) -> bool:
        """
        Unregister a tool.
        
        Args:
            name: The name of the tool to unregister.
            
        Returns:
            True if the tool was unregistered, False if it wasn't registered.
        """
        if name in self._tools:
            del self._tools[name]
            logger.debug(f"Unregistered tool: {name}")
            return True
        return False
    
    def clear(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()
        logger.debug("Cleared all registered tools")

# Create a global instance of the tool registry
tool_registry = ToolRegistry()

# Convenience functions that use the global registry
def register_tool(name: str, fn: Callable) -> None:
    """Register a tool with the global registry."""
    tool_registry.register_tool(name, fn)

def get_tool(name: str) -> Optional[Callable]:
    """Get a tool by name from the global registry."""
    return tool_registry.get_tool(name)

def get_all_tools() -> Dict[str, Callable]:
    """Get all registered tools from the global registry."""
    return tool_registry.get_all_tools()

def unregister_tool(name: str) -> bool:
    """Unregister a tool from the global registry."""
    return tool_registry.unregister_tool(name)

def clear_tools() -> None:
    """Clear all registered tools from the global registry."""
    tool_registry.clear()