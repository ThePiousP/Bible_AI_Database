# Bible AI Database API Documentation

Complete REST API for Bible AI interactions with authentication, rate limiting, and mobile app support.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Authentication](#authentication)
- [Rate Limiting](#rate-limiting)
- [Endpoints](#endpoints)
- [Security](#security)
- [Deployment](#deployment)
- [Mobile Integration](#mobile-integration)
- [Examples](#examples)

---

## Overview

The Bible AI Database API provides secure, scalable access to:
- **Semantic Search**: Vector-based search across 31,102 Bible verses
- **RAG (Retrieval-Augmented Generation)**: Question answering grounded in Scripture
- **Chat Interface**: Conversational AI for Bible discussion
- **Verse Lookup**: Direct access to specific verses

## Features

### Security
- ✅ **API Key Authentication** - Secure access control with hashed keys
- ✅ **Input Validation** - Pydantic models prevent injection attacks
- ✅ **Rate Limiting** - Token bucket algorithm prevents abuse
- ✅ **CORS Support** - Configurable cross-origin access for mobile apps
- ✅ **SQL Injection Prevention** - Sanitized query inputs
- ✅ **Prompt Injection Prevention** - Validates AI prompts

### Performance
- ✅ **GZip Compression** - Reduced bandwidth for large responses
- ✅ **Async Processing** - FastAPI's async/await for concurrency
- ✅ **Connection Pooling** - Efficient database connections
- ✅ **Response Caching** - (Coming soon) Redis-based caching

### Developer Experience
- ✅ **OpenAPI/Swagger Docs** - Interactive API documentation at `/docs`
- ✅ **Type Safety** - Pydantic models for request/response validation
- ✅ **Error Handling** - Descriptive error messages with proper HTTP codes
- ✅ **Health Checks** - Monitoring endpoints for uptime tracking

---

## Installation

### 1. Install Dependencies

```bash
# Clone repository
git clone https://github.com/ThePiousP/Bible_AI_Database.git
cd Bible_AI_Database

# Install with API dependencies
pip install -e .[api]

# Or install all dependencies (dev + AI + API)
pip install -e .[all]
```

### 2. Environment Setup

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### 3. Start Server

```bash
# Development mode (auto-reload)
bible-api --reload

# Production mode
bible-api --host 0.0.0.0 --port 8000 --workers 4

# Or use uvicorn directly
uvicorn code.api.main:app --host 0.0.0.0 --port 8000
```

### 4. Verify Installation

```bash
# Check health
curl http://localhost:8000/admin/health

# View docs
open http://localhost:8000/docs
```

---

## Configuration

### Environment Variables (.env)

```bash
# API Configuration
API_HOST=127.0.0.1
API_PORT=8000
API_WORKERS=4

# CORS - Allowed Origins (comma-separated)
ALLOWED_ORIGINS=https://myapp.com,https://app.myapp.com

# Rate Limiting
DEFAULT_RATE_LIMIT=100  # requests per minute
ANON_RATE_LIMIT=10      # unauthenticated requests

# LLM Configuration
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.7

# Embeddings
EMBEDDINGS_MODEL=all-mpnet-base-v2
EMBEDDINGS_PATH=embeddings/bible_embeddings.pkl
```

### Production Settings

For production deployment:

1. **Set specific CORS origins** (not `*`)
2. **Use HTTPS** (configure reverse proxy)
3. **Enable monitoring** (Sentry, Prometheus)
4. **Use Redis** for distributed rate limiting
5. **Increase workers** based on CPU cores

---

## Authentication

### API Key System

All endpoints (except `/admin/health`) require API key authentication.

#### Get an API Key

**Development:**
- Default key is printed when server starts
- Save it from console output

**Production:**
```bash
# Generate new API key
curl -X POST http://localhost:8000/admin/keys/create \
  -H "X-API-Key: your_admin_key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mobile App Production",
    "rate_limit": 500
  }'

# Response:
{
  "api_key": "bible_ai_xxxxxxxxxxxx",  # SAVE THIS!
  "name": "Mobile App Production",
  "rate_limit": 500,
  "created_at": "2025-11-19T10:00:00Z"
}
```

#### Using API Keys

Include in `X-API-Key` header:

```bash
curl http://localhost:8000/search/vector \
  -H "X-API-Key: bible_ai_xxxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "love",
    "top_k": 10
  }'
```

#### Key Management

```bash
# List all keys
curl http://localhost:8000/admin/keys/list \
  -H "X-API-Key: your_admin_key"

# Revoke a key
curl -X POST http://localhost:8000/admin/keys/revoke/bible_ai_ \
  -H "X-API-Key: your_admin_key"
```

---

## Rate Limiting

### How It Works

**Token Bucket Algorithm:**
- Each API key has a bucket of tokens
- Each request consumes 1 token
- Tokens refill at configured rate (default: 100/minute)
- When bucket is empty, requests are rejected with `429 Too Many Requests`

### Rate Limits

| Client Type | Default Limit | Customizable |
|-------------|---------------|--------------|
| Authenticated (API key) | 100 req/min | ✅ Yes |
| Unauthenticated (IP) | 10 req/min | ✅ Yes |
| Development key | 1000 req/min | ✅ Yes |

### Response Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
Retry-After: 30  # (if rate limited)
```

### Custom Rate Limits

```bash
# Create key with custom limit
curl -X POST http://localhost:8000/admin/keys/create \
  -H "X-API-Key: admin_key" \
  -d '{
    "name": "Enterprise Client",
    "rate_limit": 5000
  }'
```

---

## Endpoints

### Health & Stats

#### GET /admin/health
Check API health status (no auth required)

```bash
curl http://localhost:8000/admin/health

# Response:
{
  "status": "healthy",
  "version": "1.0.0",
  "database_status": "connected",
  "embeddings_loaded": true,
  "timestamp": "2025-11-19T10:00:00Z"
}
```

#### GET /admin/stats
Get database statistics (requires API key)

```bash
curl http://localhost:8000/admin/stats \
  -H "X-API-Key: your_key"

# Response:
{
  "total_verses": 31102,
  "total_books": 66,
  "total_chapters": 1189,
  "embeddings_count": 31102,
  "api_version": "1.0.0"
}
```

---

### Search Endpoints

#### POST /search/vector
Semantic vector search across Bible verses

**Request:**
```json
{
  "query": "God's love for humanity",
  "top_k": 10,
  "similarity_threshold": 0.3,
  "include_context": true,
  "filters": {
    "testament": "new"
  }
}
```

**Response:**
```json
{
  "query": "God's love for humanity",
  "results": [
    {
      "verse_id": 26137,
      "book_name": "John",
      "chapter": 3,
      "verse": 16,
      "text": "For God so loved the world...",
      "similarity_score": 0.95,
      "context": ["In the beginning...", "..."]
    }
  ],
  "total_results": 10,
  "search_time_ms": 45.2
}
```

#### POST /search/verse
Look up specific Bible verse

**Request:**
```json
{
  "book": "John",
  "chapter": 3,
  "verse": 16,
  "include_context": true
}
```

**Response:**
```json
{
  "verse": {
    "verse_id": 26137,
    "book_name": "John",
    "chapter": 3,
    "verse": 16,
    "text": "For God so loved the world...",
    "similarity_score": 1.0
  },
  "context": [...]
}
```

---

### RAG Endpoints

#### POST /rag/query
Ask questions and get answers grounded in Bible text

**Request:**
```json
{
  "question": "What does the Bible say about love?",
  "top_k": 10,
  "similarity_threshold": 0.3,
  "temperature": 0.7,
  "max_tokens": 500
}
```

**Response:**
```json
{
  "question": "What does the Bible say about love?",
  "answer": "The Bible teaches that love is patient, kind, and never fails. In 1 Corinthians 13:4-8, Paul describes...",
  "relevant_verses": [
    {
      "verse_id": 28809,
      "book_name": "1 Corinthians",
      "chapter": 13,
      "verse": 4,
      "text": "Love is patient, love is kind...",
      "similarity_score": 0.92
    }
  ],
  "confidence_score": 0.85,
  "processing_time_ms": 1250.5
}
```

#### GET /rag/demo
Get example questions

---

### Chat Endpoints

#### POST /chat/message
Send message in conversational AI chat

**Request:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Tell me about David"
    }
  ],
  "use_rag": true,
  "temperature": 0.7,
  "max_tokens": 500
}
```

**Response:**
```json
{
  "message": {
    "role": "assistant",
    "content": "David was the second king of Israel...",
    "timestamp": "2025-11-19T10:00:00Z"
  },
  "relevant_verses": [
    {
      "verse_id": 7644,
      "book_name": "1 Samuel",
      "chapter": 16,
      "verse": 13,
      "text": "So Samuel took the horn of oil...",
      "similarity_score": 0.88
    }
  ],
  "processing_time_ms": 980.3
}
```

#### GET /chat/demo
Get example conversation

---

## Security

### Input Validation

**All inputs are validated using Pydantic models:**

```python
class VectorSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(10, ge=1, le=100)

    @field_validator("query")
    @classmethod
    def sanitize_query(cls, v: str) -> str:
        # Prevents SQL injection
        dangerous_chars = [";", "--", "/*"]
        for char in dangerous_chars:
            if char in v.lower():
                raise ValueError(f"Invalid character: {char}")
        return v.strip()
```

### SQL Injection Prevention

- All database queries use parameterized statements
- Input sanitization via Pydantic validators
- No raw SQL from user input

### Prompt Injection Prevention

```python
@field_validator("question")
@classmethod
def validate_question(cls, v: str) -> str:
    # Prevents LLM prompt injection
    if any(injection in v.lower() for injection in
           ["ignore previous", "system:", "assistant:"]):
        raise ValueError("Potential prompt injection detected")
    return v.strip()
```

### HTTPS/TLS

**Production deployment MUST use HTTPS:**

```nginx
# Nginx reverse proxy example
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Host $host;
    }
}
```

---

## Deployment

### Docker Deployment

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt requirements-api.txt ./
RUN pip install --no-cache-dir -r requirements-api.txt

# Copy application
COPY . .

# Install package
RUN pip install -e .[api]

# Expose port
EXPOSE 8000

# Run server
CMD ["bible-api", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ALLOWED_ORIGINS=https://myapp.com
      - DEFAULT_RATE_LIMIT=100
    volumes:
      - ./data:/app/data
      - ./embeddings:/app/embeddings
    restart: unless-stopped
```

**Deploy:**
```bash
docker-compose up -d
```

### Cloud Deployment

#### AWS (EC2 + ALB)

```bash
# 1. Launch EC2 instance (t3.medium or larger)
# 2. Install dependencies
# 3. Configure systemd service

sudo nano /etc/systemd/system/bible-api.service
```

```ini
[Unit]
Description=Bible AI Database API
After=network.target

[Service]
Type=notify
User=ubuntu
WorkingDirectory=/home/ubuntu/Bible_AI_Database
ExecStart=/home/ubuntu/venv/bin/bible-api --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# 4. Start service
sudo systemctl enable bible-api
sudo systemctl start bible-api
```

#### Heroku

```bash
# 1. Create Procfile
echo "web: bible-api --host 0.0.0.0 --port \$PORT --workers 4" > Procfile

# 2. Deploy
heroku create bible-ai-api
git push heroku master
```

#### Google Cloud Run

```bash
# 1. Build container
gcloud builds submit --tag gcr.io/PROJECT_ID/bible-api

# 2. Deploy
gcloud run deploy bible-api \
  --image gcr.io/PROJECT_ID/bible-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

---

## Mobile Integration

### iOS (Swift)

```swift
import Foundation

class BibleAPIClient {
    private let baseURL = "https://api.yourdomain.com"
    private let apiKey = "your_api_key"

    func vectorSearch(query: String, completion: @escaping (Result<SearchResponse, Error>) -> Void) {
        guard let url = URL(string: "\(baseURL)/search/vector") else { return }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue(apiKey, forHTTPHeaderField: "X-API-Key")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body: [String: Any] = [
            "query": query,
            "top_k": 10,
            "similarity_threshold": 0.3
        ]
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)

        URLSession.shared.dataTask(with: request) { data, response, error in
            // Handle response
        }.resume()
    }
}
```

### Android (Kotlin)

```kotlin
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.*

interface BibleAPI {
    @POST("search/vector")
    suspend fun vectorSearch(
        @Header("X-API-Key") apiKey: String,
        @Body request: VectorSearchRequest
    ): SearchResponse
}

class BibleAPIClient {
    private val apiKey = "your_api_key"

    private val api = Retrofit.Builder()
        .baseUrl("https://api.yourdomain.com")
        .addConverterFactory(GsonConverterFactory.create())
        .build()
        .create(BibleAPI::class.java)

    suspend fun search(query: String): SearchResponse {
        return api.vectorSearch(
            apiKey = apiKey,
            request = VectorSearchRequest(query, topK = 10)
        )
    }
}
```

### React Native (JavaScript)

```javascript
const BIBLE_API_KEY = 'your_api_key';
const BASE_URL = 'https://api.yourdomain.com';

export const searchVerse = async (query) => {
  const response = await fetch(`${BASE_URL}/search/vector`, {
    method: 'POST',
    headers: {
      'X-API-Key': BIBLE_API_KEY,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query,
      top_k: 10,
      similarity_threshold: 0.3,
    }),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return await response.json();
};
```

---

## Examples

### Complete Search Flow

```python
import requests

API_KEY = "your_api_key"
BASE_URL = "http://localhost:8000"

# 1. Health check
response = requests.get(f"{BASE_URL}/admin/health")
print(f"API Status: {response.json()['status']}")

# 2. Vector search
search_response = requests.post(
    f"{BASE_URL}/search/vector",
    headers={"X-API-Key": API_KEY},
    json={
        "query": "faith and hope",
        "top_k": 5,
        "similarity_threshold": 0.3,
        "include_context": True
    }
)

results = search_response.json()
print(f"Found {results['total_results']} verses in {results['search_time_ms']:.2f}ms")

for verse in results['results']:
    print(f"{verse['book_name']} {verse['chapter']}:{verse['verse']}")
    print(f"  {verse['text']}")
    print(f"  Similarity: {verse['similarity_score']:.2f}\n")
```

### RAG Question Answering

```python
# Ask a question
rag_response = requests.post(
    f"{BASE_URL}/rag/query",
    headers={"X-API-Key": API_KEY},
    json={
        "question": "What does Jesus say about prayer?",
        "top_k": 10,
        "temperature": 0.7,
        "max_tokens": 500
    }
)

answer = rag_response.json()
print(f"Q: {answer['question']}")
print(f"A: {answer['answer']}\n")
print("Relevant verses:")
for verse in answer['relevant_verses']:
    print(f"  - {verse['book_name']} {verse['chapter']}:{verse['verse']}")
```

### Chat Conversation

```python
messages = [
    {"role": "user", "content": "Tell me about Moses"}
]

chat_response = requests.post(
    f"{BASE_URL}/chat/message",
    headers={"X-API-Key": API_KEY},
    json={
        "messages": messages,
        "use_rag": True,
        "temperature": 0.7
    }
)

reply = chat_response.json()
print(f"Assistant: {reply['message']['content']}")

# Continue conversation
messages.append(reply['message'])
messages.append({"role": "user", "content": "What did he do?"})
# ... make another request
```

---

## Monitoring & Observability

### Health Checks

```bash
# Kubernetes liveness probe
curl http://localhost:8000/admin/health

# Response should be 200 OK with status: healthy
```

### Metrics (Coming Soon)

```python
# Prometheus metrics at /metrics
# - request_count
# - request_duration_seconds
# - rate_limit_hits
# - database_queries
```

### Error Tracking

```bash
# Configure Sentry in .env
SENTRY_DSN=https://xxx@sentry.io/xxx
```

---

## Support

- **Documentation**: https://github.com/ThePiousP/Bible_AI_Database
- **Issues**: https://github.com/ThePiousP/Bible_AI_Database/issues
- **API Docs**: http://localhost:8000/docs (when running)

---

## License

MIT License - See LICENSE file for details
