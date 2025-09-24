# Postman API Collection for Multi-Domain Chatbot

This directory contains a comprehensive Postman collection for testing the Multi-Domain AI Chatbot API.

## Collection Overview

The `Multi_Domain_Chatbot_API.json` file contains:

### 📂 Test Categories

1. **Health & Status**
   - Root endpoint test
   - Health check endpoint

2. **Chat Operations**
   - Send chat messages
   - Retrieve chat history
   - Clear conversation history

3. **City Information Tests**
   - Test queries about different cities (Paris, New York, Tokyo)
   - Verify Wikipedia API integration

4. **Weather Information Tests**
   - Weather queries for various cities (London, San Francisco, Sydney)
   - Test OpenWeatherMap API integration

5. **Research Queries Tests**
   - Academic research searches (AI, Machine Learning, Climate Change)
   - Verify Semantic Scholar API integration

6. **Product Search Tests**
   - Product searches (laptops, iPhones, headphones, books)
   - Test PostgreSQL database integration

7. **Mixed & Complex Queries**
   - Multi-topic conversations
   - Conversational follow-ups

8. **Error Handling Tests**
   - Empty messages
   - Invalid JSON
   - Missing fields
   - Non-existent entities

9. **Load Testing**
   - Rapid fire requests with random data

## 🚀 Getting Started

### Prerequisites
- Postman installed (desktop app or web version)
- Chatbot API running locally on `http://localhost:8000`

### Import Collection

1. Open Postman
2. Click "Import" button
3. Select `Multi_Domain_Chatbot_API.json`
4. The collection will be imported with all requests and tests

### Environment Variables

The collection uses a variable:
- `base_url`: Set to `http://localhost:8000` by default
- You can modify this in the collection variables or create an environment

### Running Tests

#### Individual Tests
- Select any request from the collection
- Click "Send" to execute
- View the response and test results

#### Collection Runner
1. Right-click on the collection name
2. Select "Run collection"
3. Choose which requests to run
4. Set iterations and delays if needed
5. Click "Run Multi-Domain Chatbot API"

#### Automated Test Scripts

Each request includes automated tests that verify:
- ✅ Response times are reasonable (< 30 seconds)
- ✅ Proper HTTP status codes
- ✅ JSON response structure
- ✅ Required response fields

## 📋 Test Scenarios

### Basic Functionality
```
GET  /health                   → 200 OK
POST /api/chat                 → 200 OK with response
GET  /api/chat/history         → 200 OK with history
POST /api/chat/clear           → 200 OK with confirmation
```

### Domain-Specific Tests

#### City Queries
- "Tell me about Paris" → Wikipedia info
- "What can you tell me about New York?" → City details

#### Weather Queries
- "What's the weather like in London?" → Weather data
- "How's the weather in San Francisco today?" → Current conditions

#### Research Queries
- "Find research papers about artificial intelligence" → Academic papers
- "I need research on machine learning algorithms" → Research results

#### Product Queries
- "Do you have any laptops available?" → Product listings
- "Show me iPhone products" → iPhone inventory

### Error Scenarios
- Empty message → 400 Bad Request
- Invalid JSON → 422 Validation Error
- Non-existent city → Graceful error message
- Non-existent product → "No results found" message

## 🔧 Customization

### Adding New Tests
1. Right-click collection or folder
2. Select "Add Request"
3. Configure request details
4. Add test scripts in the "Tests" tab

### Modifying Base URL
```javascript
// In Pre-request Script or Tests tab
pm.globals.set("base_url", "https://your-api-domain.com");
```

### Custom Test Scripts
```javascript
pm.test("Response contains expected data", function () {
    const jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('response');
    pm.expect(jsonData.response).to.include('expected text');
});
```

## 📊 Expected Results

### Successful Tests
- All health checks pass
- Chat responses are returned promptly
- Domain-specific queries work correctly
- Error handling is graceful

### Performance Expectations
- Response times < 30 seconds
- No server errors (5xx codes)
- Proper validation errors for bad input

## 🐛 Troubleshooting

### Common Issues

1. **Connection refused**
   - Ensure the chatbot API is running
   - Check the base_url variable

2. **Timeout errors**
   - Increase timeout in Postman settings
   - Check external API availability (Wikipedia, weather)

3. **Database errors**
   - Ensure PostgreSQL is running
   - Run database bootstrap script

4. **OpenAI errors**
   - Check API key configuration
   - Verify account has credits

### Debug Information
- Check console logs in Postman
- Review response bodies for error details
- Monitor server logs for backend issues

## 🎯 Best Practices

1. **Run tests sequentially** for conversation flow testing
2. **Use environment variables** for different deployment environments
3. **Monitor response times** to catch performance regressions
4. **Include edge cases** in your test scenarios
5. **Document expected behaviors** in test descriptions

## 📈 Continuous Integration

This collection can be used with Newman (Postman CLI) for CI/CD:

```bash
# Install Newman
npm install -g newman

# Run collection
newman run Multi_Domain_Chatbot_API.json \
  --environment production.json \
  --reporters cli,json \
  --reporter-json-export results.json
```