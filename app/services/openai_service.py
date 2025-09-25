import json
import uuid
from typing import List, Dict, Any, Optional
from openai import OpenAI
from app.core.config import get_settings
from app.core.logging_config import get_logger, log_request_start, log_request_end, log_tool_call, log_tool_result, log_error_with_context
from app.tools.registry import get_tool_registry


class OpenAIService:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OpenAIService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if OpenAIService._initialized:
            return

        settings = get_settings()
        self.client = OpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url if settings.llm_base_url else None
        )
        self.model = settings.default_model
        self.conversations: Dict[str, List[Dict[str, Any]]] = {}
        self.logger = get_logger('app.services.openai')

        # Initialize tool registry
        self.tool_registry = get_tool_registry()
        registry_info = self.tool_registry.get_registry_info()
        self.logger.info(f"🤖 OpenAI service initialized with model: {self.model}")
        self.logger.info(f"🔧 Tool registry loaded: {registry_info['total_active']}/{registry_info['total_discovered']} tools active")
        self.logger.debug(f"🛠️ Active tools: {registry_info['active_tools']}")

        OpenAIService._initialized = True

    def get_available_functions(self) -> Dict[str, Any]:
        """Get available functions from the tool registry"""
        return self.tool_registry.get_available_functions()

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get tool definitions from the tool registry"""
        return self.tool_registry.get_openai_tool_definitions()

    def chat(self, user_message: str, conversation_id: Optional[str] = None) -> tuple[str, str]:
        """Process user message and return AI response with multi-turn tool calling"""
        # Generate conversation_id if not provided
        if conversation_id is None:
            conversation_id = str(uuid.uuid4())

        # Initialize conversation if it doesn't exist
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []

        request_id = log_request_start(self.logger, "CHAT", "OpenAI", {
            "message": user_message[:100] + "..." if len(user_message) > 100 else user_message,
            "conversation_id": conversation_id
        })

        try:
            conversation_history = self.conversations[conversation_id]
            self.logger.debug(f"💬 USER INPUT [{request_id}]: {user_message}")
            self.logger.info(f"🧠 Processing chat message for conversation {conversation_id} with {len(conversation_history)} previous messages")

            # Add user message to conversation history
            conversation_history.append({
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
                """
            }

            # Multi-turn loop for tool calling
            max_turns = 10  # Prevent infinite loops
            turn = 0
            final_message = ""

            while turn < max_turns:
                turn += 1
                self.logger.info(f"🔄 Turn {turn}/{max_turns}")

                # Prepare messages for OpenAI
                messages = [system_message] + conversation_history
                self.logger.debug(f"📤 Sending {len(messages)} messages to OpenAI")

                # Call OpenAI with tool calling
                tool_definitions = self.get_tool_definitions()
                self.logger.info(f"🤖 Calling OpenAI API ({self.model}) - Turn {turn} with {len(tool_definitions)} tools")
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=tool_definitions,
                    # in case we want to force the tool choice, default is "auto"
                    tool_choice="auto",
                    # parallel_tool_calls=False
                )

                message = response.choices[0].message
                self.logger.debug(f"📥 OpenAI response turn {turn}: tool_calls={bool(message.tool_calls)}, content_length={len(message.content or '')}")

                # Check if AI wants to call functions (new tool_calls format)
                if message.tool_calls:
                    self.logger.info(f"🔧 Turn {turn}: AI requested {len(message.tool_calls)} tool calls {', '.join([tool_call.function.name for tool_call in message.tool_calls])}")

                    # Add the assistant message with tool calls to conversation
                    conversation_history.append({
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

                        self.logger.info(f"🔧 Turn {turn}: Executing tool call {tool_call_id}: {function_name}")
                        log_tool_call(self.logger, "OpenAI", function_name, function_args)

                        try:
                            function_to_call = available_functions[function_name]
                            function_response = function_to_call(**function_args)

                            response_length = len(str(function_response))
                            log_tool_result(self.logger, "OpenAI", function_name, True, response_length)
                            self.logger.debug(f"🔧 Tool {tool_call_id} response: {str(function_response)[:200]}...")

                            # Add tool response to conversation
                            conversation_history.append({
                                "role": "tool",
                                "tool_call_id": tool_call_id,
                                "content": str(function_response)
                            })

                        except Exception as e:
                            self.logger.error(f"❌ Tool call {tool_call_id} failed: {str(e)}")
                            log_tool_result(self.logger, "OpenAI", function_name, False, 0)
                            # Add error response to conversation
                            conversation_history.append({
                                "role": "tool",
                                "tool_call_id": tool_call_id,
                                "content": f"Error executing {function_name}: {str(e)}"
                            })

                    # Continue to next turn - don't break, let AI decide what to do with the tool results
                    continue

                else:
                    # No tool calls - we have the final response
                    final_message = message.content or ''
                    self.logger.info(f"💬 Turn {turn}: Final response received (no tool calls)")

                    # Add final AI response to conversation history
                    conversation_history.append({
                        "role": "assistant",
                        "content": final_message
                    })

                    break

            # Check if we hit max turns
            if turn >= max_turns:
                self.logger.warning(f"⚠️ Reached maximum turns ({max_turns}), stopping conversation")
                if not final_message:
                    final_message = "I apologize, but I reached the maximum number of processing steps. Please try rephrasing your request."

            self.logger.debug(f"🤖 AI RESPONSE [{request_id}]: {final_message}")
            self.logger.info(f"✅ Chat completed successfully after {turn} turns, response length: {len(final_message or '')}")
            log_request_end(self.logger, request_id, 200, {"response_length": len(final_message or ''), "turns": turn, "conversation_id": conversation_id})

            return final_message, conversation_id

        except Exception as e:
            log_error_with_context(self.logger, e, "chat_processing", {
                "user_message": user_message[:100],
                "conversation_id": conversation_id,
                "conversation_length": len(self.conversations.get(conversation_id, []))
            })
            log_request_end(self.logger, request_id, 500)
            error_response = f"Sorry, I encountered an internal error. Please try again later."
            self.logger.warning(f"🚨 Error while processing chat: {str(e)}")
            return error_response, conversation_id

    def clear_conversation(self, conversation_id: Optional[str] = None):
        """Clear conversation history"""
        if conversation_id is None:
            # Clear all conversations
            total_messages = sum(len(conv) for conv in self.conversations.values())
            total_conversations = len(self.conversations)
            self.conversations = {}
            self.logger.info(f"🧹 All conversation history cleared ({total_conversations} conversations, {total_messages} messages)")
        else:
            # Clear specific conversation
            if conversation_id in self.conversations:
                previous_length = len(self.conversations[conversation_id])
                del self.conversations[conversation_id]
                self.logger.info(f"🧹 Conversation {conversation_id} cleared (was {previous_length} messages)")
            else:
                self.logger.warning(f"⚠️ Attempted to clear non-existent conversation: {conversation_id}")

    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a specific conversation_id"""
        return self.conversations.get(conversation_id, [])

    def get_conversation_count(self) -> int:
        """Get total number of active conversations"""
        return len(self.conversations)

    def get_total_message_count(self) -> int:
        """Get total number of messages across all conversations"""
        return sum(len(conv) for conv in self.conversations.values())

    def list_conversation_ids(self) -> List[str]:
        """Get list of all conversation IDs"""
        return list(self.conversations.keys())

    def cleanup_empty_conversations(self) -> int:
        """Remove conversations with no messages and return count of removed conversations"""
        empty_conversations = [conv_id for conv_id, history in self.conversations.items() if len(history) == 0]
        for conv_id in empty_conversations:
            del self.conversations[conv_id]

        if empty_conversations:
            self.logger.info(f"🧹 Cleaned up {len(empty_conversations)} empty conversations")

        return len(empty_conversations)

