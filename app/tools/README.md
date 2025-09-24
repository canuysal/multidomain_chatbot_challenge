# 🔧 Tools System

This directory contains the tools system for the Multi-Domain AI Chatbot. Tools are automatically discovered and registered, making it easy to extend the chatbot with new capabilities.

## 📋 Table of Contents
- [Overview](#overview)
- [Tool Registry](#tool-registry)
- [Available Tools](#available-tools)
- [Creating New Tools](#creating-new-tools)
- [Tool Configuration](#tool-configuration)
- [Testing Tools](#testing-tools)
- [Best Practices](#best-practices)

## 🌟 Overview

The tools system provides:
- **Automatic Discovery**: Tools are discovered and registered automatically
- **Selective Loading**: Control which tools are active using environment variables
- **Standardized Interface**: All tools inherit from `BaseTool` for consistency
- **OpenAI Integration**: Seamless integration with OpenAI function calling
- **Extensible Architecture**: Easy to add new tools without modifying existing code

## 🏗️ Architecture

```
app/tools/
├── base/
│   ├── __init__.py
│   └── base_tool.py          # Abstract base class for all tools
├── registry.py               # Tool discovery and management
├── city_tool.py             # Wikipedia city information
├── weather_tool.py          # OpenWeatherMap integration
├── research_tool.py         # Semantic Scholar academic search
├── product_tool.py          # Database product search
└── README.md               # This file
```

## 🔍 Tool Registry

The `ToolRegistry` class handles:
- **Automatic Discovery**: Scans the tools directory for tool classes
- **Validation**: Ensures tools implement required methods
- **Selective Loading**: Respects `ACTIVE_TOOLS` environment variable
- **OpenAI Integration**: Provides function definitions and mappings

### Registry Usage

```python
from app.tools.registry import get_tool_registry

# Get the global registry instance
registry = get_tool_registry()

# Get registry information
info = registry.get_registry_info()
print(f"Active tools: {info['active_tools']}")

# Get available functions for OpenAI
functions = registry.get_available_functions()
tool_definitions = registry.get_openai_tool_definitions()
```

## 🛠️ Available Tools

| Tool | Function | Description |
|------|----------|-------------|
| **City** | `get_city_info` | Fetch city information from Wikipedia |
| **Weather** | `get_weather` | Get weather data from OpenWeatherMap |
| **Research** | `search_research` | Search academic papers via Semantic Scholar |
| **Product** | `find_products` | Search products in the database |

## 🚀 Creating New Tools

### Step 1: Create Tool Class

Create a new file in the `app/tools/` directory (e.g., `my_tool.py`):

```python
from typing import Dict, Any
from app.tools.base.base_tool import BaseTool

class MyTool(BaseTool):
    \"\"\"Description of what your tool does\"\"\"

    def __init__(self):
        super().__init__()
        # Initialize your tool-specific attributes
        self.api_endpoint = "https://api.example.com"

    def get_tool_name(self) -> str:
        \"\"\"Return unique tool identifier (lowercase)\"\"\"
        return "mytool"

    def get_tool_description(self) -> str:
        \"\"\"Return human-readable description\"\"\"
        return "Tool for doing something awesome"

    def get_openai_function_schema(self) -> Dict[str, Any]:
        \"\"\"Define the OpenAI function calling schema\"\"\"
        return {
            "type": "function",
            "function": {
                "name": "my_function",
                "description": "What this function does",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "input_param": {
                            "type": "string",
                            "description": "Description of the parameter"
                        }
                    },
                    "required": ["input_param"],
                    "additionalProperties": False
                },
                "strict": True
            }
        }

    def get_function_mapping(self) -> Dict[str, callable]:
        \"\"\"Map function names to implementations\"\"\"
        return {
            "my_function": self.my_function
        }

    def my_function(self, input_param: str) -> str:
        \"\"\"Implement your tool's functionality\"\"\"
        try:
            # Your tool logic here
            result = f"Processed: {input_param}"
            self.logger.info(f"✅ Successfully processed: {input_param}")
            return result
        except Exception as e:
            self.logger.error(f"❌ Error processing {input_param}: {str(e)}")
            return f"Error: {str(e)}"

# Create instance for registry (optional, but recommended)
my_tool = MyTool()
```

### Step 2: Tool Discovery

That's it! The tool will be automatically discovered and registered when the application starts.

### Step 3: Test Your Tool

```python
# Test the tool directly
from app.tools.my_tool import my_tool

result = my_tool.my_function("test input")
print(result)

# Test via registry
from app.tools.registry import get_tool_registry

registry = get_tool_registry()
info = registry.get_registry_info()
print(f"Your tool active: {'mytool' in info['active_tools']}")
```

## ⚙️ Tool Configuration

### Environment Variables

Control which tools are active using the `ACTIVE_TOOLS` environment variable:

```bash
# Load all tools (default)
# No ACTIVE_TOOLS environment variable needed

# Load specific tools only
export ACTIVE_TOOLS="city,weather"

# Load single tool
export ACTIVE_TOOLS="product"
```

### Configuration in .env File

```env
# .env file
ACTIVE_TOOLS=city,weather,research
```

### Programmatic Configuration

```python
import os
from app.tools.registry import reload_tool_registry

# Change active tools at runtime
os.environ['ACTIVE_TOOLS'] = 'city,product'
reload_tool_registry()
```

## 🧪 Testing Tools

### Unit Testing

Create tests in `tests/test_tools/`:

```python
import pytest
from app.tools.my_tool import MyTool

class TestMyTool:
    def setup_method(self):
        self.tool = MyTool()

    def test_tool_name(self):
        assert self.tool.get_tool_name() == "mytool"

    def test_tool_validation(self):
        assert self.tool.validate_tool() is True

    def test_function_execution(self):
        result = self.tool.my_function("test")
        assert "Processed: test" in result

    def test_error_handling(self):
        # Test error scenarios
        pass
```

### Integration Testing

Test with the registry:

```python
def test_tool_registry_integration():
    from app.tools.registry import get_tool_registry

    registry = get_tool_registry()
    tools = registry.get_active_tools()

    assert "mytool" in tools

    functions = registry.get_available_functions()
    assert "my_function" in functions
```

### Manual Testing

```bash
# Test tool discovery
python -c "
from app.tools.registry import get_tool_registry
registry = get_tool_registry()
print(registry.get_registry_info())
"

# Test with specific tools
ACTIVE_TOOLS=mytool python -c "
from app.tools.registry import get_tool_registry
registry = get_tool_registry()
print('Active:', registry.get_registry_info()['active_tools'])
"
```

## 📝 Best Practices

### 1. Naming Conventions
- **Tool Names**: lowercase, descriptive (e.g., `weather`, `database`, `email`)
- **Function Names**: snake_case, verb-based (e.g., `get_weather`, `send_email`)
- **File Names**: `{tool_name}_tool.py` (e.g., `weather_tool.py`)

### 2. Error Handling
- Always use try-catch blocks in your tool functions
- Log errors with context using `self.logger`
- Return user-friendly error messages
- Never let exceptions bubble up unhandled

```python
def my_function(self, param: str) -> str:
    try:
        # Tool logic
        return "Success"
    except SpecificError as e:
        self.logger.error(f"❌ Specific error: {str(e)}")
        return "User-friendly error message"
    except Exception as e:
        self.logger.error(f"❌ Unexpected error: {str(e)}")
        return "An unexpected error occurred"
```

### 3. Logging
- Use structured logging with emojis for readability
- Log at appropriate levels (DEBUG, INFO, WARNING, ERROR)
- Include context in log messages

```python
self.logger.info(f"🔍 Searching for: {query}")
self.logger.debug(f"📡 API request to: {url}")
self.logger.warning(f"⚠️ Rate limit approaching")
self.logger.error(f"❌ API call failed: {error}")
```

### 4. Function Schemas
- Use detailed parameter descriptions
- Set `"strict": True` for OpenAI function calling
- Include all required parameters
- Set `"additionalProperties": False` to prevent extra parameters

### 5. Response Formatting
- Return human-readable responses
- Use consistent formatting (emojis, headers, bullets)
- Limit response length for better UX
- Handle empty results gracefully

### 6. Validation
- Implement custom validation in `validate_tool()` if needed
- Validate input parameters before processing
- Check for required dependencies in `__init__`

### 7. Documentation
- Include comprehensive docstrings
- Document parameter types and return values
- Provide usage examples
- Document any external dependencies

## 🔧 Advanced Features

### Multi-Function Tools

A single tool can provide multiple functions:

```python
def get_openai_function_schema(self) -> Dict[str, Any]:
    return [
        {
            "type": "function",
            "function": {
                "name": "search_function",
                # ... search function schema
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_details_function",
                # ... details function schema
            }
        }
    ]

def get_function_mapping(self) -> Dict[str, callable]:
    return {
        "search_function": self.search,
        "get_details_function": self.get_details
    }
```

### Tool Dependencies

Check for dependencies in validation:

```python
def validate_tool(self) -> bool:
    # Call parent validation first
    if not super().validate_tool():
        return False

    # Check for API keys
    if not self.api_key:
        self.logger.error("❌ API key not configured")
        return False

    # Check for database connection
    try:
        # Test connection
        return True
    except Exception as e:
        self.logger.error(f"❌ Database connection failed: {e}")
        return False
```

### Dynamic Tool Loading

Tools can be loaded dynamically from external packages or plugins.

## 🚨 Troubleshooting

### Tool Not Discovered
- Check file naming convention
- Ensure class inherits from `BaseTool`
- Verify no syntax errors in tool file
- Check logs for import errors

### Tool Not Active
- Check `ACTIVE_TOOLS` environment variable
- Verify tool name matches `get_tool_name()` return value
- Check tool validation passes

### Function Not Available
- Ensure function exists in `get_function_mapping()`
- Verify OpenAI schema matches function name
- Check for exceptions during tool initialization

### Debug Tool Registry

```python
from app.tools.registry import get_tool_registry

registry = get_tool_registry()
info = registry.get_registry_info()

print("Registry Info:")
print(f"  Total discovered: {info['total_discovered']}")
print(f"  Total active: {info['total_active']}")
print(f"  Active tools: {info['active_tools']}")
print(f"  Inactive tools: {info['inactive_tools']}")
print(f"  ACTIVE_TOOLS env: {info['active_tools_env']}")
```

---

## 🤝 Contributing

1. Follow the naming conventions and best practices
2. Write comprehensive tests for your tools
3. Update this README when adding new tools
4. Ensure your tool validates correctly
5. Test both individual functions and registry integration

For questions or issues, check the main project README or create an issue in the repository.