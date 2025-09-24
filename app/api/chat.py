from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from app.services.openai_service import OpenAIService

router = APIRouter()
openai_service = OpenAIService()


class ChatMessage(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    conversation_id: str = "default"


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat_message: ChatMessage):
    """
    Main chat endpoint for API access
    """
    try:
        if not chat_message.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")

        response = openai_service.chat(chat_message.message)

        return ChatResponse(
            response=response,
            conversation_id="default"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")


@router.post("/chat/clear")
async def clear_chat_endpoint():
    """
    Clear conversation history
    """
    try:
        openai_service.clear_conversation()
        return {"message": "Conversation cleared successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing conversation: {str(e)}")


@router.get("/chat/history")
async def get_chat_history():
    """
    Get current conversation history
    """
    try:
        return {
            "history": openai_service.conversation_history,
            "message_count": len(openai_service.conversation_history)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving history: {str(e)}")