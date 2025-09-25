from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.services.openai_service import OpenAIService
from app.core.logging_config import get_logger, log_request_start, log_request_end, log_error_with_context

router = APIRouter()
openai_service = OpenAIService()
logger = get_logger('app.api.chat')


class CustomTool(BaseModel):
    name: str
    endpoint: str
    description: str


class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    filter_tools: Optional[List[str]] = None
    custom_api: Optional[CustomTool] = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: str


class ClearChatRequest(BaseModel):
    conversation_id: Optional[str] = None


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat_message: ChatMessage):
    """
    Main chat endpoint for API access
    filter_tools is an array of tool names to enable, options: city, weather, research, product
    custom_api is an object with the name, endpoint, and description of the custom API tool to enable
    if filter_tools is not provided, all tools are enabled
    set conversation_id to a specific value to use a specific conversation
    """
    request_id = log_request_start(logger, "POST", "/api/chat", {
        "message_length": len(chat_message.message),
        "conversation_id": chat_message.conversation_id
    })

    try:
        logger.info(f"💬 Chat API request received")
        logger.debug(f"📝 Message preview: {chat_message.message[:100]}...")

        if not chat_message.message.strip():
            logger.warning("❌ Empty message received in chat API")
            log_request_end(logger, request_id, 400)
            raise HTTPException(status_code=400, detail="Message cannot be empty")

        logger.info(f"🔄 Processing chat message via OpenAI service")
        response, conversation_id = openai_service.chat(chat_message.message, chat_message.conversation_id, chat_message.filter_tools, chat_message.custom_api)

        response_obj = ChatResponse(
            response=response,
            conversation_id=conversation_id
        )

        logger.info(f"✅ Chat API request completed successfully")
        logger.debug(f"📤 Response length: {len(response)}")
        log_request_end(logger, request_id, 200, {"response_length": len(response), "conversation_id": conversation_id})

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
async def clear_chat_endpoint(clear_request: ClearChatRequest = None):
    """
    Clear conversation history
    """
    conversation_id = clear_request.conversation_id if clear_request else None
    request_id = log_request_start(logger, "POST", "/api/chat/clear", {"conversation_id": conversation_id})

    try:
        logger.info("🧹 Chat clear request received")
        openai_service.clear_conversation(conversation_id)

        if conversation_id:
            message = f"Conversation {conversation_id} cleared successfully"
        else:
            message = "All conversations cleared successfully"

        logger.info("✅ Chat history cleared successfully")
        log_request_end(logger, request_id, 200)
        return {"message": message}

    except Exception as e:
        log_error_with_context(logger, e, "clear_chat_endpoint")
        log_request_end(logger, request_id, 500)
        logger.error(f"🚨 Clear chat API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error clearing conversation: {str(e)}")


@router.get("/chat/history")
async def get_chat_history(conversation_id: Optional[str] = None):
    """
    Get current conversation history
    """
    request_id = log_request_start(logger, "GET", "/api/chat/history", {"conversation_id": conversation_id})

    try:
        logger.info("📋 Chat history request received")

        if conversation_id:
            history = openai_service.get_conversation_history(conversation_id)
            message_count = len(history)
        else:
            # Return all conversations
            all_conversations = openai_service.conversations
            total_conversations = len(all_conversations)
            total_messages = sum(len(conv) for conv in all_conversations.values())

            logger.info(f"✅ Retrieved all chat history: {total_conversations} conversations, {total_messages} messages")
            log_request_end(logger, request_id, 200, {"total_conversations": total_conversations, "total_messages": total_messages})

            return {
                "conversations": all_conversations,
                "total_conversations": total_conversations,
                "total_messages": total_messages
            }

        logger.info(f"✅ Retrieved chat history for conversation {conversation_id} with {message_count} messages")
        logger.debug(f"📊 History preview: {[msg.get('role', 'unknown') for msg in history[:5]]}")
        log_request_end(logger, request_id, 200, {"message_count": message_count, "conversation_id": conversation_id})

        return {
            "history": history,
            "message_count": message_count,
            "conversation_id": conversation_id
        }

    except Exception as e:
        log_error_with_context(logger, e, "get_chat_history_endpoint")
        log_request_end(logger, request_id, 500)
        logger.error(f"🚨 Get history API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving history: {str(e)}")


@router.get("/chat/stats")
async def get_conversation_stats():
    """
    Get conversation statistics
    """
    request_id = log_request_start(logger, "GET", "/api/chat/stats")

    try:
        logger.info("📊 Conversation stats request received")

        conversation_count = openai_service.get_conversation_count()
        total_messages = openai_service.get_total_message_count()
        conversation_ids = openai_service.list_conversation_ids()

        stats = {
            "total_conversations": conversation_count,
            "total_messages": total_messages,
            "conversation_ids": conversation_ids,
            "average_messages_per_conversation": round(total_messages / conversation_count, 2) if conversation_count > 0 else 0
        }

        logger.info(f"✅ Retrieved conversation stats: {conversation_count} conversations, {total_messages} messages")
        log_request_end(logger, request_id, 200, stats)

        return stats

    except Exception as e:
        log_error_with_context(logger, e, "get_conversation_stats_endpoint")
        log_request_end(logger, request_id, 500)
        logger.error(f"🚨 Get stats API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving stats: {str(e)}")


@router.post("/chat/cleanup")
async def cleanup_conversations():
    """
    Cleanup empty conversations
    """
    request_id = log_request_start(logger, "POST", "/api/chat/cleanup")

    try:
        logger.info("🧹 Conversation cleanup request received")

        cleaned_count = openai_service.cleanup_empty_conversations()

        logger.info(f"✅ Conversation cleanup completed: {cleaned_count} conversations removed")
        log_request_end(logger, request_id, 200, {"cleaned_conversations": cleaned_count})

        return {"message": f"Cleaned up {cleaned_count} empty conversations", "cleaned_conversations": cleaned_count}

    except Exception as e:
        log_error_with_context(logger, e, "cleanup_conversations_endpoint")
        log_request_end(logger, request_id, 500)
        logger.error(f"🚨 Cleanup API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during cleanup: {str(e)}")