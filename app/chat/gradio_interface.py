import gradio as gr
from app.services.openai_service import OpenAIService
from app.core.logging_config import get_logger


class ChatInterface:
    def __init__(self):
        self.openai_service = OpenAIService()
        self.logger = get_logger('app.chat.gradio')

    def chat_function(self, message: str, history: list) -> tuple:
        """Process user message and return response for Gradio"""
        self.logger.info("🎨 Gradio chat request received")
        self.logger.debug(f"📝 Message: {message[:100]}...")

        if not message.strip():
            self.logger.warning("❌ Empty message in Gradio interface")
            return history, ""

        try:
            # Get response from OpenAI service
            self.logger.info("🔄 Processing message via OpenAI service")
            response = self.openai_service.chat(message)

            # Update history
            history.append((message, response))

            self.logger.info(f"✅ Gradio chat completed successfully")
            self.logger.debug(f"📤 Response length: {len(response)}")

            return history, ""

        except Exception as e:
            self.logger.error(f"🚨 Gradio chat error: {str(e)}")
            error_response = f"Sorry, I encountered an error: {str(e)}"
            history.append((message, error_response))
            return history, ""

    def clear_chat(self):
        """Clear both Gradio and OpenAI conversation history"""
        self.logger.info("🧹 Gradio chat clear requested")
        self.openai_service.clear_conversation()
        self.logger.info("✅ Gradio chat cleared successfully")
        return []

    def create_interface(self):
        """Create and return Gradio interface"""
        with gr.Blocks(title="AI Chatbot", theme=gr.themes.Soft()) as interface:
            gr.Markdown("# 🤖 Multi-Domain AI Chatbot")
            gr.Markdown("Ask me about cities, weather, research topics, or products!")

            chatbot = gr.Chatbot(
                value=[],
                elem_id="chatbot",
                bubble_full_width=False,
                height=500
            )

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
                inputs=None,
                outputs=chatbot
            )

        return interface


def create_chat_interface():
    """Factory function to create chat interface"""
    chat_interface = ChatInterface()
    return chat_interface.create_interface()