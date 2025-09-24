from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from app.core.logging_config import get_logger


class BaseTool(ABC):
    """
    Abstract base class for all tools in the system.

    All tools should inherit from this class and implement the required methods.
    This provides a consistent interface for tool registration, execution, and metadata.
    """

    def __init__(self):
        self.logger = get_logger(f'app.tools.{self.get_tool_name()}')
        self.logger.info(f"🔧 {self.get_tool_name()} tool initialized")

    @abstractmethod
    def get_tool_name(self) -> str:
        """
        Return the unique identifier/name for this tool.
        This should be lowercase and match the function name in OpenAI schema.

        Returns:
            str: Tool identifier (e.g., "city", "weather", "research", "product")
        """
        pass

    @abstractmethod
    def get_tool_description(self) -> str:
        """
        Return a human-readable description of what this tool does.

        Returns:
            str: Tool description for documentation and UI
        """
        pass

    @abstractmethod
    def get_openai_function_schema(self) -> Dict[str, Any]:
        """
        Return the OpenAI function calling schema for this tool.
        This defines the function signature that OpenAI will use to call the tool.

        Returns:
            Dict[str, Any]: OpenAI function schema in the required format
        """
        pass

    @abstractmethod
    def get_function_mapping(self) -> Dict[str, callable]:
        """
        Return a mapping of function names to their callable implementations.
        The keys should match the function names in the OpenAI schema.

        Returns:
            Dict[str, callable]: Mapping of function name to callable
        """
        pass

    def get_tool_version(self) -> str:
        """
        Return the version of this tool.
        Override this method if you need custom versioning.

        Returns:
            str: Tool version
        """
        return "1.0.0"

    def get_tool_metadata(self) -> Dict[str, Any]:
        """
        Return metadata about this tool for registry and documentation.

        Returns:
            Dict[str, Any]: Tool metadata
        """
        return {
            "name": self.get_tool_name(),
            "description": self.get_tool_description(),
            "version": self.get_tool_version(),
            "functions": list(self.get_function_mapping().keys()),
            "openai_schema": self.get_openai_function_schema()
        }

    def validate_tool(self) -> bool:
        """
        Validate that the tool is properly configured and ready to use.
        Override this method to add custom validation logic.

        Returns:
            bool: True if tool is valid, False otherwise
        """
        try:
            # Basic validation
            name = self.get_tool_name()
            description = self.get_tool_description()
            schema = self.get_openai_function_schema()
            functions = self.get_function_mapping()

            if not name or not isinstance(name, str):
                self.logger.error("❌ Tool name is invalid")
                return False

            if not description or not isinstance(description, str):
                self.logger.error("❌ Tool description is invalid")
                return False

            if not schema or not isinstance(schema, dict):
                self.logger.error("❌ OpenAI schema is invalid")
                return False

            if not functions or not isinstance(functions, dict):
                self.logger.error("❌ Function mapping is invalid")
                return False

            # Validate that all functions in schema are available in mapping
            schema_functions = []
            if isinstance(schema, list):
                schema_functions = [func.get("function", {}).get("name") for func in schema]
            elif "function" in schema:
                schema_functions = [schema["function"]["name"]]

            for func_name in schema_functions:
                if func_name not in functions:
                    self.logger.error(f"❌ Function '{func_name}' in schema but not in mapping")
                    return False

            self.logger.debug(f"✅ Tool '{name}' validation passed")
            return True

        except Exception as e:
            self.logger.error(f"❌ Tool validation failed: {str(e)}")
            return False

    def __str__(self) -> str:
        """String representation of the tool"""
        return f"{self.__class__.__name__}({self.get_tool_name()})"

    def __repr__(self) -> str:
        """Developer representation of the tool"""
        return f"{self.__class__.__name__}(name='{self.get_tool_name()}', version='{self.get_tool_version()}')"