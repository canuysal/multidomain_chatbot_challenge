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
        self.conversation_history: List[Dict[str, Any]] = []
        self.logger = get_logger('app.services.openai')

    def get_available_functions(self) -> Dict[str, Any]:
        """Define available functions for the AI to use"""
        return {
            "get_city_info": city_tool.get_city_info,
            "get_weather": weather_tool.get_weather,
            "search_research": research_tool.search_research,
            "find_products": product_tool.find_products
        }

    def get_function_definitions(self) -> List[Dict[str, Any]]:
        """Define function schemas for OpenAI function calling"""
        return [
            {
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
                    "required": ["city_name"]
                }
            },
            {
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
                    "required": ["city_name"]
                }
            },
            {
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
                    "required": ["topic"]
                }
            },
            {
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
                    "required": ["query"]
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

                Always greet users warmly and be helpful. Use the available functions when appropriate to provide accurate information."""
            }

            # Prepare messages for OpenAI
            messages = [system_message] + self.conversation_history
            self.logger.debug(f"📤 Sending {len(messages)} messages to OpenAI")

            # Call OpenAI with function calling
            self.logger.info("🤖 Calling OpenAI API for initial response")
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                functions=self.get_function_definitions(),
                function_call="auto"
            )

            message = response.choices[0].message
            self.logger.debug(f"📥 OpenAI response: function_call={bool(message.function_call)}, content_length={len(message.content or '')}")

            # Check if AI wants to call a function
            if message.function_call:
                function_name = message.function_call.name
                function_args = json.loads(message.function_call.arguments)

                self.logger.info(f"🔧 AI requested function call: {function_name}")
                log_tool_call(self.logger, "OpenAI", function_name, function_args)

                # Execute the function
                available_functions = self.get_available_functions()
                function_to_call = available_functions[function_name]

                self.logger.info(f"⚡ Executing tool function: {function_name}")
                function_response = function_to_call(**function_args)

                response_length = len(str(function_response))
                log_tool_result(self.logger, "OpenAI", function_name, True, response_length)
                self.logger.debug(f"🔧 Tool response preview: {str(function_response)[:200]}...")

                # Add function call and response to conversation
                self.conversation_history.append({
                    "role": "assistant",
                    "content": None,
                    "function_call": {
                        "name": function_name,
                        "arguments": message.function_call.arguments
                    }
                })

                self.conversation_history.append({
                    "role": "function",
                    "name": function_name,
                    "content": str(function_response)
                })

                # Get final response from AI
                self.logger.info("🤖 Calling OpenAI API for final response")
                final_response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[system_message] + self.conversation_history
                )

                final_message = final_response.choices[0].message.content
            else:
                final_message = message.content
                self.logger.info("💬 Direct response (no function call needed)")

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

