import json
from typing import List, Dict, Any, Optional
from openai import OpenAI
from app.core.config import get_settings
from app.core.logging_config import get_logger, log_request_start, log_request_end, log_tool_call, log_tool_result, log_error_with_context
from app.tools.city_tool import city_tool
from app.tools.weather_tool import weather_tool
from app.tools.research_tool import research_tool
from app.tools.product_tool import product_tool


class OpenAIService:
    def __init__(self):
        settings = get_settings()
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.default_model
        self.conversation_history: List[Dict[str, Any]] = []
        self.logger = get_logger('app.services.openai')
        self.logger.info(f"🤖 OpenAI service initialized with model: {self.model}")

    def get_available_functions(self) -> Dict[str, Any]:
        """Define available functions for the AI to use"""
        return {
            "get_city_info": city_tool.get_city_info,
            "get_weather": weather_tool.get_weather,
            "search_research": research_tool.search_research,
            "find_products": product_tool.find_products
        }

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Define tool schemas for OpenAI tool calling"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_city_info",
                    "description": "Get general information about a city using Wikipedia",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city_name": {
                                "type": "string",
                                "description": "Name of the city to get information about"
                            }
                        },
                        "required": ["city_name"],
                        "additionalProperties": False
                    },
                    "strict": True
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get current weather conditions for a specific city",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city_name": {
                                "type": "string",
                                "description": "Name of the city to get weather for"
                            }
                        },
                        "required": ["city_name"],
                        "additionalProperties": False
                        }
                },
                    "strict": True
            },
            {
                "type": "function",
                "function": {
                    "name": "search_research",
                    "description": "Search for academic research papers and information on a topic",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "topic": {
                                "type": "string",
                                "description": "Research topic or subject to search for"
                            }
                        },
                        "required": ["topic"],
                        "additionalProperties": False,
                    },
                    "strict": True
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "find_products",
                    "description": "Search for products in the database by name, description, category, or brand",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Product name, description, category, or brand to search for"
                            }
                        },
                        "required": ["query"],
                        "additionalProperties": False,
                    },
                    "strict": True
                }
            }
        ]

    def chat(self, user_message: str) -> str:
        """Process user message and return AI response"""
        request_id = log_request_start(self.logger, "CHAT", "OpenAI", {"message": user_message[:100] + "..." if len(user_message) > 100 else user_message})

        try:
            self.logger.debug(f"💬 USER INPUT [{request_id}]: {user_message}")
            self.logger.info(f"🧠 Processing chat message with {len(self.conversation_history)} previous messages")

            # Add user message to conversation history
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })

            # Create system message
            system_message = {
                "role": "system",
                "content": """You are a helpful chatbot that can assist users with:
                - Information about cities (using Wikipedia)
                - Weather information for cities
                - Research topics and academic information
                - Product searches from our database

                Always greet users warmly and be helpful. Use the available functions when appropriate to provide accurate information.
                If you don't have the information, inform the user that you don't have the information and try to suggest other ways to get the information.
                If the function returns an error, inform the user about the nature of the error, e.g. rate limit, timeout, internal server error, etc.
                While using get_city_info function, add the url of the wikipedia page to response.
                Do not use markdown formatting in the response.
                """
            }

            # Prepare messages for OpenAI
            messages = [system_message] + self.conversation_history
            self.logger.debug(f"📤 Sending {len(messages)} messages to OpenAI")

            # Call OpenAI with function calling
            self.logger.info(f"🤖 Calling OpenAI API ({self.model}) for initial response")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.get_tool_definitions(),
                tool_choice="auto"
            )

            message = response.choices[0].message
            self.logger.debug(f"📥 OpenAI response: tool_calls={bool(message.tool_calls)}, content_length={len(message.content or '')}")

            self.logger.debug(f"📥 OpenAI response: {message}")

            # Check if AI wants to call functions (new tool_calls format)
            if message.tool_calls:
                self.logger.info(f"🔧 AI requested {len(message.tool_calls)} tool calls")

                # Add the assistant message with tool calls to conversation
                self.conversation_history.append({
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": tool_call.type,
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments
                            }
                        }
                        for tool_call in message.tool_calls
                    ]
                })

                # Execute each tool call
                available_functions = self.get_available_functions()

                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    tool_call_id = tool_call.id

                    self.logger.info(f"🔧 Executing tool call {tool_call_id}: {function_name}")
                    log_tool_call(self.logger, "OpenAI", function_name, function_args)

                    try:
                        function_to_call = available_functions[function_name]
                        function_response = function_to_call(**function_args)

                        response_length = len(str(function_response))
                        log_tool_result(self.logger, "OpenAI", function_name, True, response_length)
                        self.logger.debug(f"🔧 Tool {tool_call_id} response: {str(function_response)[:200]}...")

                        # Add tool response to conversation
                        self.conversation_history.append({
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "content": str(function_response)
                        })

                    except Exception as e:
                        self.logger.error(f"❌ Tool call {tool_call_id} failed: {str(e)}")
                        # Add error response to conversation
                        self.conversation_history.append({
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "content": f"Error executing {function_name}: {str(e)}"
                        })

                # Get final response from AI after all tool calls
                self.logger.info(f"🤖 Calling OpenAI API ({self.model}) for final response after {len(message.tool_calls)} tool calls")
                final_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[system_message] + self.conversation_history
                )

                final_message = final_response.choices[0].message.content or ''
            else:
                final_message = message.content or ''
                self.logger.info("💬 Direct response (no tool calls needed)")

            # Add AI response to conversation history
            self.conversation_history.append({
                "role": "assistant",
                "content": final_message
            })

            self.logger.debug(f"🤖 AI RESPONSE [{request_id}]: {final_message}")
            self.logger.info(f"✅ Chat completed successfully, response length: {len(final_message or '')}")
            log_request_end(self.logger, request_id, 200, {"response_length": len(final_message or '')})

            return final_message

        except Exception as e:
            log_error_with_context(self.logger, e, "chat_processing", {
                "user_message": user_message[:100],
                "conversation_length": len(self.conversation_history)
            })
            log_request_end(self.logger, request_id, 500)
            error_response = f"Sorry, I encountered an error: {str(e)}"
            self.logger.warning(f"🚨 Returning error response: {error_response}")
            return error_response

    def clear_conversation(self):
        """Clear conversation history"""
        previous_length = len(self.conversation_history)
        self.conversation_history = []
        self.logger.info(f"🧹 Conversation history cleared (was {previous_length} messages)")

