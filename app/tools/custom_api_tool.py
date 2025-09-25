import requests
from typing import Optional, Dict, Any
import json
from app.utils.error_handlers import handle_tool_errors, log_request_response, APIConnectionError
from app.core.logging_config import log_request_start, log_request_end, log_error_with_context
from app.tools.base.base_tool import BaseTool


class CustomAPITool(BaseTool):
    """Dynamic tool for calling custom API endpoints"""

    def __init__(self, name: str, endpoint: str, description: str):
        self.tool_name = name
        self.api_endpoint = endpoint
        self.tool_description = description
        super().__init__()

    @handle_tool_errors("Custom API")
    @log_request_response("CustomAPITool")
    def call_api(self) -> str:
        """
        Call the custom API endpoint

        Returns:
            str: API response or error message
        """
        request_id = log_request_start(self.logger, "GET", self.api_endpoint, {"tool_name": self.tool_name})

        try:
            self.logger.info(f"🔧 Calling custom API: {self.tool_name} -> {self.api_endpoint}")

            headers = {
                'User-Agent': 'MultiDomainChatbot/1.0 (https://example.com/contact)',
                'Accept': 'application/json'
            }

            self.logger.info(f"📡 Custom API request to: {self.api_endpoint}")
            response = requests.get(self.api_endpoint, headers=headers, timeout=30)
            self.logger.info(f"📥 Custom API response: {response.status_code}")

            if response.status_code == 200:
                try:
                    # Try to parse as JSON
                    data = response.json()
                    self.logger.info(f"✅ Successfully fetched data from {self.tool_name}")
                    self.logger.info(f"🔍 Custom API response data: {json.dumps(data, indent=2)}")
                    result = self._format_api_response(data)
                    log_request_end(self.logger, request_id, 200, {"response_length": len(result)})
                    return result
                except json.JSONDecodeError:
                    # Return raw text if not JSON
                    result = response.text
                    self.logger.info(f"✅ Successfully fetched text data from {self.tool_name}")
                    log_request_end(self.logger, request_id, 200, {"response_length": len(result)})
                    return result

            else:
                self.logger.error(f"❌ Custom API error: {response.status_code}")
                log_request_end(self.logger, request_id, response.status_code)
                return f"Sorry, the {self.tool_name} API returned an error (status {response.status_code}). Please try again later."

        except requests.exceptions.Timeout:
            log_error_with_context(self.logger, Exception("Request timeout"), "Custom API call", {"endpoint": self.api_endpoint})
            log_request_end(self.logger, request_id, 408)
            return f"The {self.tool_name} API request timed out. Please try again."

        except requests.exceptions.ConnectionError:
            log_error_with_context(self.logger, Exception("Connection error"), "Custom API call", {"endpoint": self.api_endpoint})
            log_request_end(self.logger, request_id, 503)
            return f"Unable to connect to the {self.tool_name} API. Please check the endpoint URL."

        except requests.exceptions.RequestException as e:
            log_error_with_context(self.logger, e, "Custom API request", {"endpoint": self.api_endpoint})
            log_request_end(self.logger, request_id, 500)
            return f"An error occurred while calling the {self.tool_name} API: {str(e)}"

        except Exception as e:
            log_error_with_context(self.logger, e, "custom_api_processing", {"endpoint": self.api_endpoint})
            log_request_end(self.logger, request_id, 500)
            return f"An unexpected error occurred: {str(e)}"

    def _format_api_response(self, data: Any) -> str:
        """
        Format the API response into a readable format

        Args:
            data: API response data

        Returns:
            str: Formatted response
        """
        try:
            if isinstance(data, dict):
                # Handle common joke API format
                if 'setup' in data and 'punchline' in data:
                    return f"🤣 **{data.get('setup')}**\n\n{data.get('punchline')}"
                elif 'joke' in data:
                    return f"🤣 {data.get('joke')}"
                else:
                    # Generic dict formatting
                    formatted_lines = []
                    for key, value in data.items():
                        if isinstance(value, (str, int, float, bool)):
                            formatted_lines.append(f"**{key.title()}**: {value}")
                    return "\n".join(formatted_lines) if formatted_lines else json.dumps(data, indent=2)

            elif isinstance(data, list):
                if len(data) > 0 and isinstance(data[0], dict):
                    # Format list of objects
                    result = []
                    for i, item in enumerate(data[:5]):  # Limit to first 5 items
                        result.append(f"**Item {i+1}**: {json.dumps(item, indent=2)}")
                    return "\n\n".join(result)
                else:
                    return "\n".join(str(item) for item in data[:10])  # Limit to first 10 items

            else:
                return str(data)

        except Exception as e:
            return f"Response received, but couldn't format it properly: {json.dumps(data, indent=2)}"

    def get_tool_name(self) -> str:
        """Return the tool identifier"""
        return self.tool_name.lower().replace(" ", "_")

    def get_tool_description(self) -> str:
        """Return tool description"""
        return self.tool_description

    def get_openai_function_schema(self) -> Dict[str, Any]:
        """Return OpenAI function schema"""
        return {
            "type": "function",
            "function": {
                "name": self.get_tool_name(),
                "description": self.get_tool_description(),
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                    "additionalProperties": False
                },
                "strict": True
            }
        }

    def get_function_mapping(self) -> Dict[str, callable]:
        """Return function mapping"""
        return {
            self.get_tool_name(): self.call_api
        }