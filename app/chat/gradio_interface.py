import gradio as gr
import uuid
from app.services.openai_service import OpenAIService
from app.core.logging_config import get_logger


class ChatInterface:
    def __init__(self):
        self.openai_service = OpenAIService()
        self.logger = get_logger('app.chat.gradio')

    def chat_function(self, message: str, history: list, request: gr.Request) -> tuple:
        """Process user message and return response for Gradio (using messages format)"""
        # Get or create conversation_id for this session
        if hasattr(request, 'session_hash'):
            conversation_id = f"gradio_{request.session_hash}"
        else:
            conversation_id = f"gradio_{str(uuid.uuid4())}"

        self.logger.info("🎨 Gradio chat request received")
        self.logger.debug(f"📝 Message: {message[:100]}...")
        self.logger.debug(f"🔑 Session conversation_id: {conversation_id}")

        if not message.strip():
            self.logger.warning("❌ Empty message in Gradio interface")
            return history, ""

        try:
            # Get response from OpenAI service
            self.logger.info(f"🔄 Processing message via OpenAI service (conversation: {conversation_id})")
            response, _ = self.openai_service.chat(message, conversation_id)

            # Update history using messages format
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": response})

            self.logger.info(f"✅ Gradio chat completed successfully")
            self.logger.debug(f"📤 Response length: {len(response)}")

            return history, ""

        except Exception as e:
            self.logger.error(f"🚨 Gradio chat error: {str(e)}")
            error_response = f"Sorry, I encountered an error: {str(e)}"
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": error_response})
            return history, ""

    def clear_chat(self, request: gr.Request):
        """Clear both Gradio and OpenAI conversation history"""
        # Get conversation_id for this session
        if hasattr(request, 'session_hash'):
            conversation_id = f"gradio_{request.session_hash}"
        else:
            conversation_id = f"gradio_{str(uuid.uuid4())}"

        self.logger.info(f"🧹 Gradio chat clear requested (conversation: {conversation_id})")
        self.openai_service.clear_conversation(conversation_id)
        self.logger.info(f"✅ Conversation {conversation_id} cleared")

        # Return welcome message when clearing chat (using messages format)
        welcome_message = """👋 **Welcome back to the Multi-Domain AI Chatbot!**

I'm ready to help you with:

🏙️ **Cities** | 🌤️ **Weather** | 📚 **Research** | 🛍️ **Products**

What would you like to know about today?"""

        self.logger.info("✅ Gradio chat cleared successfully, showing welcome message")
        return [{"role": "assistant", "content": welcome_message}]

    def create_interface(self):
        """Create and return Gradio interface"""
        self.logger.info("🎨 Creating Gradio chat interface with welcome message")

        # Welcome message to display on page load
        welcome_message = """👋 **Welcome to the Multi-Domain AI Chatbot!**

I'm here to help you with information across multiple domains:

🏙️ **Cities**: Ask me about any city worldwide - I'll fetch information from Wikipedia
🌤️ **Weather**: Get current weather conditions for any location
📚 **Research**: Search for academic papers and research on any topic
🛍️ **Products**: Browse our product database and find items you're looking for

**Try asking me:**
- "Tell me about Paris"
- "What's the weather like in Tokyo?"
- "Find research papers about machine learning"
- "Do you have any laptops for sale?"

Feel free to ask me anything! I can handle multiple topics in a single conversation. 🚀"""

        with gr.Blocks(title="AI Chatbot", theme=gr.themes.Soft()) as interface:
            gr.Markdown("# 🤖 Multi-Domain AI Chatbot")
            gr.Markdown("Ask me about cities, weather, research topics, or products!")

            # Session info will be updated dynamically
            session_info = gr.Markdown("**Session ID:** `Connecting...`", elem_classes="session-info")

            chatbot = gr.Chatbot(
                value=[{"role": "assistant", "content": welcome_message}],
                elem_id="chatbot",
                type="messages",
                height=500,
                show_label=False,
            )

            chatbot.clear(self.clear_chat, inputs=None, outputs=chatbot)

            with gr.Row():
                msg = gr.Textbox(
                    placeholder="Type your message here...",
                    container=False,
                    scale=4,
                    label="Message"
                )
                send_btn = gr.Button("Send", scale=1, variant="primary")

            with gr.Row():
                clear_btn = gr.Button("Clear Chat", variant="secondary")

            # Function to update session info
            def update_session_info(request: gr.Request):
                if hasattr(request, 'session_hash'):
                    conversation_id = f"gradio_{request.session_hash}"
                else:
                    conversation_id = f"gradio_{str(uuid.uuid4())}"
                return f"**Session ID:** `{conversation_id}`"

            # Update session info on page load
            interface.load(
                fn=update_session_info,
                outputs=session_info
            )

            # Set up event handlers
            send_btn.click(
                fn=self.chat_function,
                inputs=[msg, chatbot],
                outputs=[chatbot, msg]
            )

            msg.submit(
                fn=self.chat_function,
                inputs=[msg, chatbot],
                outputs=[chatbot, msg]
            )

            clear_btn.click(
                fn=self.clear_chat,
                outputs=chatbot
            )

        return interface


def create_chat_interface():
    """Factory function to create chat interface"""
    chat_interface = ChatInterface()
    return chat_interface.create_interface()