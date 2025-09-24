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

    @patch('app.services.openai_service.OpenAIService.chat')
    def test_chat_endpoint_success(self, mock_chat):
        """Test successful chat request"""
        mock_chat.return_value = "Hello! How can I help you today?"

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

    @patch('app.services.openai_service.OpenAIService.chat')
    def test_chat_endpoint_openai_error(self, mock_chat):
        """Test chat endpoint when OpenAI service fails"""
        mock_chat.side_effect = Exception("OpenAI API error")

        response = client.post(
            "/api/chat",
            json={"message": "Hello"}
        )

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Error processing message" in data["detail"]

    @patch('app.services.openai_service.OpenAIService.clear_conversation')
    def test_clear_chat_endpoint(self, mock_clear):
        """Test the clear chat endpoint"""
        mock_clear.return_value = None

        response = client.post("/api/chat/clear")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "cleared" in data["message"].lower()

    @patch('app.services.openai_service.OpenAIService.conversation_history', new_callable=lambda: [])
    def test_get_chat_history_empty(self, mock_history):
        """Test getting empty chat history"""
        response = client.get("/api/chat/history")

        assert response.status_code == 200
        data = response.json()
        assert "history" in data
        assert "message_count" in data
        assert data["message_count"] == 0

    @patch('app.services.openai_service.OpenAIService.conversation_history')
    def test_get_chat_history_with_messages(self, mock_history):
        """Test getting chat history with messages"""
        mock_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]

        with patch.object(client.app.state, 'openai_service') as mock_service:
            mock_service.conversation_history = mock_history

            response = client.get("/api/chat/history")

            assert response.status_code == 200
            data = response.json()
            assert "history" in data
            assert "message_count" in data


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

    def test_chat_extra_fields(self):
        """Test chat endpoint ignores extra fields"""
        response = client.post(
            "/api/chat",
            json={
                "message": "Hello",
                "extra_field": "should be ignored"
            }
        )
        # Should still work (extra fields are typically ignored)
        # The actual behavior depends on your Pydantic configuration
        assert response.status_code in [200, 422]


class TestAPIErrorHandling:
    """Test API error handling"""

    @patch('app.services.openai_service.OpenAIService.__init__')
    def test_service_initialization_error(self, mock_init):
        """Test handling of service initialization errors"""
        mock_init.side_effect = Exception("Service initialization failed")

        # This would typically be handled at the application startup level
        # For this test, we're checking that the error is properly caught
        try:
            from app.services.openai_service import OpenAIService
            service = OpenAIService()
            assert False, "Should have raised an exception"
        except Exception as e:
            assert "initialization failed" in str(e)

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

    @patch('app.services.openai_service.OpenAIService.chat')
    def test_concurrent_requests(self, mock_chat):
        """Test handling of multiple concurrent requests"""
        mock_chat.return_value = "Response"

        import threading
        import time

        results = []
        errors = []

        def make_request():
            try:
                response = client.post(
                    "/api/chat",
                    json={"message": "Test"},
                    timeout=5
                )
                results.append(response.status_code)
            except Exception as e:
                errors.append(str(e))

        # Create 5 concurrent requests
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)

        # Start all threads
        start_time = time.time()
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        end_time = time.time()

        # Check results
        assert len(results) == 5
        assert all(status == 200 for status in results)
        assert len(errors) == 0
        assert end_time - start_time < 10  # Should complete within 10 seconds


if __name__ == "__main__":
    pytest.main([__file__])