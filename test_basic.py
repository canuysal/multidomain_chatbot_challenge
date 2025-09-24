#!/usr/bin/env python3
"""
Basic test script to verify OpenAI integration works
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.openai_service import OpenAIService


def test_openai_service():
    """Test the OpenAI service with mock functions"""
    print("🧪 Testing OpenAI Service...")

    try:
        service = OpenAIService()

        # Test basic conversation
        print("\n1. Testing basic greeting:")
        response = service.chat("Hello!")
        print(f"Response: {response}")

        # Test function calling (should trigger mock functions)
        print("\n2. Testing city query:")
        response = service.chat("Tell me about Paris")
        print(f"Response: {response}")

        print("\n3. Testing weather query:")
        response = service.chat("What's the weather like in London?")
        print(f"Response: {response}")

        print("\n4. Testing research query:")
        response = service.chat("Find research about artificial intelligence")
        print(f"Response: {response}")

        print("\n5. Testing product query:")
        response = service.chat("Do you have any laptops?")
        print(f"Response: {response}")

        print("\n✅ Basic OpenAI service test completed!")
        return True

    except Exception as e:
        print(f"❌ Error testing OpenAI service: {str(e)}")
        return False


if __name__ == "__main__":
    if test_openai_service():
        print("\n🎉 All basic tests passed!")
    else:
        print("\n💥 Some tests failed!")
        sys.exit(1)