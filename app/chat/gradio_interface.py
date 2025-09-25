import gradio as gr
import uuid
from app.services.openai_service import OpenAIService
from app.core.logging_config import get_logger
from app.api.chat import CustomTool, CustomParameter


class ChatInterface:
    def __init__(self):
        self.openai_service = OpenAIService()
        self.logger = get_logger('app.chat.gradio')

    def render_param_rows(self, params):
        """Render HTML for parameter rows"""
        if not params:
            return "<div style='color: #888; font-style: italic;'>No parameters defined</div>"

        html = "<div>"
        for i, param in enumerate(params):
            name = param.get('name', '')
            desc = param.get('description', '')
            required = param.get('required', False)

            html += f"""
            <div style='border: 1px solid #ddd; border-radius: 8px; padding: 12px; margin: 8px 0; background: #f9f9f9;'>
                <div style='display: flex; align-items: center; gap: 12px; margin-bottom: 8px;'>
                    <div style='flex: 1;'>
                        <label style='font-weight: bold; color: #333;'>Name:</label>
                        <input type='text' value='{name}' placeholder='parameter_name'
                               style='width: 100%; padding: 4px 8px; border: 1px solid #ccc; border-radius: 4px; margin-top: 2px;'
                               onchange='updateParam({i}, "name", this.value)'>
                    </div>
                    <div style='flex: 2;'>
                        <label style='font-weight: bold; color: #333;'>Description:</label>
                        <input type='text' value='{desc}' placeholder='Parameter description'
                               style='width: 100%; padding: 4px 8px; border: 1px solid #ccc; border-radius: 4px; margin-top: 2px;'
                               onchange='updateParam({i}, "description", this.value)'>
                    </div>
                    <div style='display: flex; align-items: center; gap: 8px;'>
                        <label style='font-weight: bold; color: #333;'>
                            <input type='checkbox' {'checked' if required else ''}
                                   onchange='updateParam({i}, "required", this.checked)'
                                   style='margin-right: 4px;'>
                            Required
                        </label>
                        <button onclick='removeParam({i})'
                                style='background: #ff4444; color: white; border: none; border-radius: 4px;
                                       padding: 4px 8px; cursor: pointer; font-size: 12px;'>❌</button>
                    </div>
                </div>
            </div>
            """
        html += "</div>"

        return html

    def chat_function(self, message: str, history: list, city_enabled: bool, weather_enabled: bool,
                     research_enabled: bool, product_enabled: bool, custom_api_enabled: bool,
                     custom_api_name: str, custom_api_endpoint: str, custom_api_description: str,
                     parameters_data: str, request: gr.Request) -> tuple:
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
            # Create filter_tools array based on enabled checkboxes
            filter_tools = []
            if city_enabled:
                filter_tools.append('city')
            if weather_enabled:
                filter_tools.append('weather')
            if research_enabled:
                filter_tools.append('research')
            if product_enabled:
                filter_tools.append('product')

            # Create custom API tool if enabled
            custom_api = None
            if custom_api_enabled and custom_api_name and custom_api_endpoint:
                # Parse parameters data (JSON format)
                parameters = []
                if parameters_data:
                    try:
                        import json
                        param_list = json.loads(parameters_data)
                        for param in param_list:
                            if param.get('name'):
                                parameters.append(CustomParameter(
                                    name=param['name'],
                                    description=param.get('description', ''),
                                    required=param.get('required', False)
                                ))
                    except json.JSONDecodeError:
                        self.logger.warning(f"Failed to parse parameters data: {parameters_data}")

                custom_api = CustomTool(
                    name=custom_api_name,
                    endpoint=custom_api_endpoint,
                    description=custom_api_description,
                    parameters=parameters if parameters else None
                )

            # Get response from OpenAI service
            self.logger.info(f"🔄 Processing message via OpenAI service (conversation: {conversation_id})")
            self.logger.debug(f"🛠️ Filter tools: {filter_tools}, custom_api: {'enabled' if custom_api else 'disabled'}")
            response, _ = self.openai_service.chat(message, conversation_id, filter_tools, custom_api)

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

            # Tool selection checkboxes
            gr.Markdown("### 🛠️ Available Tools")
            with gr.Row():
                city_tool = gr.Checkbox(label="🏙️ Cities", value=True)
                weather_tool = gr.Checkbox(label="🌤️ Weather", value=True)
                research_tool = gr.Checkbox(label="📚 Research", value=True)
                product_tool = gr.Checkbox(label="🛍️ Products", value=True)

            # Custom API tool section
            gr.Markdown("### 🔧 Custom API Tool")
            with gr.Column():
                custom_api_enabled = gr.Checkbox(label="Custom API (Only GET Requests, 30s timeout)", value=True)
                with gr.Row():
                    custom_api_name = gr.Textbox(
                        label="Tool Name",
                        value="search_repositories",
                        placeholder="Enter custom tool name...",
                        scale=2
                    )
                    custom_api_endpoint = gr.Textbox(
                        label="API Endpoint",
                        value="https://api.github.com/search/repositories",
                        placeholder="https://api.example.com/endpoint",
                        scale=3
                    )
                custom_api_description = gr.Textbox(
                    label="Description",
                    value="Search GitHub Repositories for a topic. In your response, list repositories by name, description and html_url if available. Sort by stars, descending unless specified otherwise.",
                    placeholder="Describe what this API does...",
                    lines=2
                )

                # Parameters section
                with gr.Column():
                    with gr.Row():
                        gr.Markdown("**Parameters**")
                        add_param_btn = gr.Button("➕ Add Parameter", size="sm", variant="secondary")

                    # Create multiple parameter rows with GitHub API defaults
                    param_rows = []
                    default_params = [
                        {"name": "q", "desc": "Query to search for", "required": True, "visible": True},
                        {"name": "sort", "desc": "Sort options, can be one of \"stars\", \"forks\" or \"updated\"", "required": False, "visible": True},
                        {"name": "order", "desc": "can be either \"asc\" or \"desc\" asc - ascending desc - descending", "required": False, "visible": True},
                        {"name": "", "desc": "", "required": False, "visible": False},
                        {"name": "", "desc": "", "required": False, "visible": False}
                    ]

                    for i in range(5):  # Support up to 5 parameters
                        default = default_params[i]
                        with gr.Row(visible=default["visible"]) as row:
                            param_name = gr.Textbox(label=f"Name", scale=2, placeholder="parameter_name", value=default["name"])
                            param_desc = gr.Textbox(label=f"Description", scale=3, placeholder="Parameter description", value=default["desc"])
                            param_required = gr.Checkbox(label="Required", scale=1, value=default["required"])
                            remove_btn = gr.Button("❌", size="sm", variant="secondary", scale=1)

                        param_rows.append({
                            'row': row,
                            'name': param_name,
                            'desc': param_desc,
                            'required': param_required,
                            'remove_btn': remove_btn
                        })

                    # Track which rows are visible - start with 3 for GitHub API
                    visible_count = gr.State(3)

                    # Hidden field to collect all parameters as JSON - initialized with GitHub API params
                    initial_params = [
                        {"name": "q", "description": "Query to search for", "required": True},
                        {"name": "sort", "description": "Sort options, can be one of \"stars\", \"forks\" or \"updated\"", "required": False},
                        {"name": "order", "description": "can be either \"asc\" or \"desc\" asc - ascending desc - descending", "required": False}
                    ]
                    import json
                    parameters_data = gr.Textbox(value=json.dumps(initial_params), visible=False)

                    def add_parameter_row(current_count):
                        """Show next parameter row"""
                        if current_count < len(param_rows):
                            new_count = current_count + 1
                            # Return visibility states for all rows
                            visibility = [gr.update(visible=True) if i < new_count else gr.update() for i in range(len(param_rows))]
                            return [new_count] + visibility
                        return [current_count] + [gr.update() for _ in range(len(param_rows))]

                    def remove_parameter_row(current_count):
                        """Hide a parameter row"""
                        if current_count > 0:
                            new_count = current_count - 1
                            # Clear the values and hide the last visible row
                            visibility = [gr.update(visible=True) if i < new_count else gr.update(visible=False) for i in range(len(param_rows))]
                            return [new_count] + visibility
                        return [current_count] + [gr.update() for _ in range(len(param_rows))]

                    def collect_parameters(*args):
                        """Collect all parameter data into JSON"""
                        current_count = args[0]
                        params = []
                        for i in range(current_count):
                            name = args[1 + i * 3]  # name, desc, required for each param
                            desc = args[1 + i * 3 + 1]
                            required = args[1 + i * 3 + 2]
                            if name:  # Only add if name is not empty
                                params.append({
                                    "name": name,
                                    "description": desc or "",
                                    "required": required
                                })
                        import json
                        return json.dumps(params)

                    # Add parameter button click
                    add_param_btn.click(
                        fn=add_parameter_row,
                        inputs=[visible_count],
                        outputs=[visible_count] + [row['row'] for row in param_rows]
                    )

                    # Remove button clicks
                    for i, row in enumerate(param_rows):
                        row['remove_btn'].click(
                            fn=remove_parameter_row,
                            inputs=[visible_count],
                            outputs=[visible_count] + [r['row'] for r in param_rows]
                        )

                    # Collect parameters on any change
                    param_inputs = [visible_count]
                    for row in param_rows:
                        param_inputs.extend([row['name'], row['desc'], row['required']])

                    for row in param_rows:
                        row['name'].change(fn=collect_parameters, inputs=param_inputs, outputs=[parameters_data])
                        row['desc'].change(fn=collect_parameters, inputs=param_inputs, outputs=[parameters_data])
                        row['required'].change(fn=collect_parameters, inputs=param_inputs, outputs=[parameters_data])

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
                inputs=[msg, chatbot, city_tool, weather_tool, research_tool, product_tool,
                       custom_api_enabled, custom_api_name, custom_api_endpoint, custom_api_description, parameters_data],
                outputs=[chatbot, msg]
            )

            msg.submit(
                fn=self.chat_function,
                inputs=[msg, chatbot, city_tool, weather_tool, research_tool, product_tool,
                       custom_api_enabled, custom_api_name, custom_api_endpoint, custom_api_description, parameters_data],
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