import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import json

# Import the FastAPI app
from main import app

client = TestClient(app)


class TestChatAPI:
    """Test cases for the chat API endpoints"""

    def test_root_endpoint(self):
        """Test the root endpoint returns correct information"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "endpoints" in data
        assert "chatbot" in data["message"].lower()

    def test_health_check(self):
        """Test the health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "chatbot" in data["service"]

    @patch('app.api.chat.openai_service')
    def test_chat_endpoint_success(self, mock_service):
        """Test successful chat request"""
        mock_service.chat.return_value = "Hello! How can I help you today?"

        response = client.post(
            "/api/chat",
            json={"message": "Hello"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "Hello!" in data["response"]
        assert "conversation_id" in data

    def test_chat_endpoint_empty_message(self):
        """Test chat endpoint with empty message"""
        response = client.post(
            "/api/chat",
            json={"message": ""}
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "empty" in data["detail"]

    def test_chat_endpoint_missing_message(self):
        """Test chat endpoint with missing message field"""
        response = client.post(
            "/api/chat",
            json={}
        )

        assert response.status_code == 422  # Validation error

    @patch('app.api.chat.openai_service')
    def test_chat_endpoint_openai_error(self, mock_service):
        """Test chat endpoint when OpenAI service fails"""
        mock_service.chat.side_effect = Exception("OpenAI API error")

        response = client.post(
            "/api/chat",
            json={"message": "Hello"}
        )

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Error processing message" in data["detail"]

    @patch('app.api.chat.openai_service')
    def test_clear_chat_endpoint(self, mock_service):
        """Test the clear chat endpoint"""
        mock_service.clear_conversation.return_value = None

        response = client.post("/api/chat/clear")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "cleared" in data["message"].lower()

    @patch('app.api.chat.openai_service')
    def test_get_chat_history_empty(self, mock_service):
        """Test getting empty chat history"""
        mock_service.conversation_history = []

        response = client.get("/api/chat/history")

        assert response.status_code == 200
        data = response.json()
        assert "history" in data
        assert "message_count" in data
        assert data["message_count"] == 0

    @patch('app.api.chat.openai_service')
    def test_get_chat_history_with_messages(self, mock_service):
        """Test getting chat history with messages"""
        mock_service.conversation_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]

        response = client.get("/api/chat/history")

        assert response.status_code == 200
        data = response.json()
        assert "history" in data
        assert "message_count" in data
        assert data["message_count"] == 2


class TestAPIValidation:
    """Test API input validation"""

    def test_chat_message_validation(self):
        """Test chat message validation"""
        # Test with invalid JSON
        response = client.post(
            "/api/chat",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_chat_message_type_validation(self):
        """Test chat message type validation"""
        # Test with wrong message type
        response = client.post(
            "/api/chat",
            json={"message": 123}  # Should be string
        )
        assert response.status_code == 422



class TestAPIErrorHandling:
    """Test API error handling"""


    def test_malformed_request(self):
        """Test handling of malformed requests"""
        response = client.post("/api/chat")  # No JSON body
        assert response.status_code == 422

        response = client.put("/api/chat")  # Wrong HTTP method
        assert response.status_code == 405

    def test_nonexistent_endpoint(self):
        """Test handling of non-existent endpoints"""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404

        response = client.post("/api/chat/nonexistent")
        assert response.status_code == 404


class TestAPIPerformance:
    """Basic performance and load tests"""



if __name__ == "__main__":
    pytest.main([__file__])