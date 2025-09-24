from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from app.services.openai_service import OpenAIService
from app.core.logging_config import get_logger, log_request_start, log_request_end, log_error_with_context

router = APIRouter()
openai_service = OpenAIService()
logger = get_logger('app.api.chat')


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
    request_id = log_request_start(logger, "POST", "/api/chat", {"message_length": len(chat_message.message)})

    try:
        logger.info(f"💬 Chat API request received")
        logger.debug(f"📝 Message preview: {chat_message.message[:100]}...")

        if not chat_message.message.strip():
            logger.warning("❌ Empty message received in chat API")
            log_request_end(logger, request_id, 400)
            raise HTTPException(status_code=400, detail="Message cannot be empty")

        logger.info(f"🔄 Processing chat message via OpenAI service")
        response = openai_service.chat(chat_message.message)

        response_obj = ChatResponse(
            response=response,
            conversation_id="default"
        )

        logger.info(f"✅ Chat API request completed successfully")
        logger.debug(f"📤 Response length: {len(response)}")
        log_request_end(logger, request_id, 200, {"response_length": len(response)})

        return response_obj

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        log_error_with_context(logger, e, "chat_api_endpoint", {"message": chat_message.message[:100]})
        log_request_end(logger, request_id, 500)
        logger.error(f"🚨 Chat API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")


@router.post("/chat/clear")
async def clear_chat_endpoint():
    """
    Clear conversation history
    """
    request_id = log_request_start(logger, "POST", "/api/chat/clear")

    try:
        logger.info("🧹 Chat clear request received")
        openai_service.clear_conversation()

        logger.info("✅ Chat history cleared successfully")
        log_request_end(logger, request_id, 200)
        return {"message": "Conversation cleared successfully"}

    except Exception as e:
        log_error_with_context(logger, e, "clear_chat_endpoint")
        log_request_end(logger, request_id, 500)
        logger.error(f"🚨 Clear chat API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error clearing conversation: {str(e)}")


@router.get("/chat/history")
async def get_chat_history():
    """
    Get current conversation history
    """
    request_id = log_request_start(logger, "GET", "/api/chat/history")

    try:
        logger.info("📋 Chat history request received")

        history = openai_service.conversation_history
        message_count = len(history)

        logger.info(f"✅ Retrieved chat history with {message_count} messages")
        logger.debug(f"📊 History preview: {[msg.get('role', 'unknown') for msg in history[:5]]}")
        log_request_end(logger, request_id, 200, {"message_count": message_count})

        return {
            "history": history,
            "message_count": message_count
        }

    except Exception as e:
        log_error_with_context(logger, e, "get_chat_history_endpoint")
        log_request_end(logger, request_id, 500)
        logger.error(f"🚨 Get history API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving history: {str(e)}")