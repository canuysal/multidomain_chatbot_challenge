import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.chat import router as chat_router
from app.chat.gradio_interface import create_chat_interface
import gradio as gr

# Create FastAPI app
app = FastAPI(
    title="Multi-Domain AI Chatbot",
    description="A chatbot that can handle cities, weather, research, and product queries",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(chat_router, prefix="/api", tags=["chat"])

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Multi-Domain AI Chatbot API",
        "endpoints": {
            "chat": "/api/chat",
            "clear_chat": "/api/chat/clear",
            "chat_history": "/api/chat/history",
            "gradio_ui": "/gradio"
        }
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "chatbot-api"}

# Create Gradio interface
gradio_app = create_chat_interface()

# Mount Gradio app
app = gr.mount_gradio_app(app, gradio_app, path="/gradio")

if __name__ == "__main__":
    print("🤖 Starting Multi-Domain AI Chatbot...")
    print("📱 Gradio UI: http://localhost:8000/gradio")
    print("🔗 API Docs: http://localhost:8000/docs")
    print("❤️  Health Check: http://localhost:8000/health")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )