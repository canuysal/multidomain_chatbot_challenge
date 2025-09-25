import importlib
import inspect
from typing import Dict, List, Any, Optional, Type
from pathlib import Path
from app.tools.base.base_tool import BaseTool
from app.core.config import get_settings
from app.core.logging_config import get_logger


class ToolRegistry:
    """
    Registry for automatic tool discovery and management.

    This class handles:
    - Automatic discovery of tools in the tools directory
    - Selective tool loading based on ACTIVE_TOOLS environment variable
    - Tool validation and instance management
    - Interface for OpenAI service integration
    """

    def __init__(self):
        self.logger = get_logger('app.tools.registry')
        self._tools: Dict[str, BaseTool] = {}
        self._tool_classes: Dict[str, Type[BaseTool]] = {}
        self.settings = get_settings()

        self.logger.info("🔧 Tool registry initializing...")
        self._discover_tools()
        self._load_active_tools()
        self.logger.info(f"✅ Tool registry initialized with {len(self._tools)} active tools")

    def _discover_tools(self):
        """Discover all available tool classes in the tools directory"""
        tools_dir = Path(__file__).parent
        self.logger.debug(f"🔍 Discovering tools in: {tools_dir}")

        # Skip base directory and __pycache__
        skip_dirs = {'base', '__pycache__', 'registry.py', '__init__.py', 'custom_api_tool.py'}

        discovered_count = 0
        for py_file in tools_dir.glob("*.py"):
            if py_file.name.startswith('_') or py_file.name in skip_dirs:
                continue

            try:
                # Import the module
                module_name = f"app.tools.{py_file.stem}"
                self.logger.debug(f"📦 Importing module: {module_name}")
                module = importlib.import_module(module_name)

                # Find classes that inherit from BaseTool
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (issubclass(obj, BaseTool) and
                        obj is not BaseTool and
                        obj.__module__ == module_name):

                        # Create instance to get tool name
                        try:
                            instance = obj()
                            tool_name = instance.get_tool_name()

                            if tool_name in self._tool_classes:
                                self.logger.warning(f"⚠️ Duplicate tool name '{tool_name}' found in {name}")
                                continue

                            self._tool_classes[tool_name] = obj
                            discovered_count += 1
                            self.logger.info(f"✅ Discovered tool: {tool_name} ({name})")

                        except Exception as e:
                            self.logger.error(f"❌ Failed to instantiate tool {name}: {str(e)}")
                            continue

            except Exception as e:
                self.logger.error(f"❌ Failed to import {py_file.name}: {str(e)}")
                continue

        self.logger.info(f"🔍 Tool discovery complete: {discovered_count} tools found")
        self.logger.info(f"📋 Available tools: {list(self._tool_classes.keys())}")

    def _load_active_tools(self):
        """Load only the tools specified in ACTIVE_TOOLS or all if not specified"""
        active_tools_env = getattr(self.settings, 'active_tools', None)

        if active_tools_env:
            # Parse comma-separated tool names
            requested_tools = [name.strip().lower() for name in active_tools_env.split(',')]
            self.logger.info(f"🎯 ACTIVE_TOOLS specified: {requested_tools}")

            # Validate requested tools exist
            available_tools = list(self._tool_classes.keys())
            valid_tools = []
            invalid_tools = []

            for tool_name in requested_tools:
                if tool_name in self._tool_classes:
                    valid_tools.append(tool_name)
                else:
                    invalid_tools.append(tool_name)

            if invalid_tools:
                self.logger.warning(f"⚠️ Invalid tools in ACTIVE_TOOLS: {invalid_tools}")
                self.logger.info(f"📋 Available tools: {available_tools}")

            tools_to_load = valid_tools
        else:
            # Load all discovered tools
            tools_to_load = list(self._tool_classes.keys())
            self.logger.info("🌍 ACTIVE_TOOLS not set, loading all discovered tools")

        # Load the selected tools
        loaded_count = 0
        failed_count = 0

        for tool_name in tools_to_load:
            try:
                tool_class = self._tool_classes[tool_name]
                instance = tool_class()

                # Validate the tool
                if instance.validate_tool():
                    self._tools[tool_name] = instance
                    loaded_count += 1
                    self.logger.debug(f"✅ Loaded tool: {tool_name}")
                else:
                    self.logger.error(f"❌ Tool validation failed: {tool_name}")
                    failed_count += 1

            except Exception as e:
                self.logger.error(f"❌ Failed to load tool '{tool_name}': {str(e)}")
                failed_count += 1

        # Log summary
        if active_tools_env:
            self.logger.info(f"🎯 Active tools loaded: {loaded_count}/{len(tools_to_load)}")
            if len(self._tool_classes) > loaded_count:
                inactive_tools = set(self._tool_classes.keys()) - set(self._tools.keys())
                self.logger.info(f"😴 Inactive tools: {list(inactive_tools)}")
        else:
            self.logger.info(f"🌍 All tools loaded: {loaded_count}/{len(self._tool_classes)}")

        if failed_count > 0:
            self.logger.warning(f"⚠️ {failed_count} tools failed to load")

    def get_active_tools(self) -> Dict[str, BaseTool]:
        """
        Get all active tool instances.

        Returns:
            Dict[str, BaseTool]: Dictionary mapping tool names to instances
        """
        return self._tools.copy()

    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """
        Get a specific tool by name.

        Args:
            tool_name (str): Name of the tool to retrieve

        Returns:
            Optional[BaseTool]: Tool instance or None if not found
        """
        return self._tools.get(tool_name.lower())

    def get_available_functions(self) -> Dict[str, callable]:
        """
        Get all available functions from active tools for OpenAI integration.

        Returns:
            Dict[str, callable]: Mapping of function names to callables
        """
        functions = {}

        for tool_name, tool in self._tools.items():
            try:
                tool_functions = tool.get_function_mapping()
                for func_name, func in tool_functions.items():
                    if func_name in functions:
                        self.logger.warning(f"⚠️ Duplicate function name '{func_name}' from tool '{tool_name}'")
                    functions[func_name] = func

            except Exception as e:
                self.logger.error(f"❌ Failed to get functions from tool '{tool_name}': {str(e)}")

        return functions

    def get_openai_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Get OpenAI tool definitions for all active tools.

        Returns:
            List[Dict[str, Any]]: List of OpenAI tool definitions
        """
        definitions = []

        for tool_name, tool in self._tools.items():
            try:
                schema = tool.get_openai_function_schema()

                # Ensure schema is in list format for multiple functions
                if isinstance(schema, dict):
                    # Single function schema
                    definitions.append(schema)
                elif isinstance(schema, list):
                    # Multiple functions schema
                    definitions.extend(schema)
                else:
                    self.logger.error(f"❌ Invalid schema format from tool '{tool_name}'")

            except Exception as e:
                self.logger.error(f"❌ Failed to get schema from tool '{tool_name}': {str(e)}")

        return definitions

    def get_registry_info(self) -> Dict[str, Any]:
        """
        Get information about the current registry state.

        Returns:
            Dict[str, Any]: Registry information for debugging/monitoring
        """
        return {
            "total_discovered": len(self._tool_classes),
            "total_active": len(self._tools),
            "discovered_tools": list(self._tool_classes.keys()),
            "active_tools": list(self._tools.keys()),
            "inactive_tools": list(set(self._tool_classes.keys()) - set(self._tools.keys())),
            "active_tools_env": getattr(self.settings, 'active_tools', None),
            "total_functions": len(self.get_available_functions())
        }

    def reload_tools(self):
        """
        Reload all tools. Useful for development or configuration changes.
        """
        self.logger.info("🔄 Reloading tools...")
        self._tools.clear()
        self._tool_classes.clear()
        self._discover_tools()
        self._load_active_tools()
        self.logger.info(f"✅ Tools reloaded: {len(self._tools)} active tools")

    def __str__(self) -> str:
        """String representation of the registry"""
        return f"ToolRegistry(active={len(self._tools)}, discovered={len(self._tool_classes)})"

    def __repr__(self) -> str:
        """Developer representation of the registry"""
        return f"ToolRegistry(active_tools={list(self._tools.keys())}, discovered_tools={list(self._tool_classes.keys())})"


# Global registry instance
_registry_instance: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """
    Get the global tool registry instance.
    Creates the instance if it doesn't exist.

    Returns:
        ToolRegistry: The global tool registry
    """
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ToolRegistry()
    return _registry_instance


def reload_tool_registry():
    """
    Force reload of the global tool registry.
    Useful for development or when configuration changes.
    """
    global _registry_instance
    if _registry_instance is not None:
        _registry_instance.reload_tools()
    else:
        _registry_instance = ToolRegistry()