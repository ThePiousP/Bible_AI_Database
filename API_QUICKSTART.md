# Bible AI API - Quick Start Guide

Get your Bible AI API running in **5 minutes**!

## 🚀 Installation

### 1. Clone & Install

```bash
# Clone repository
git clone https://github.com/ThePiousP/Bible_AI_Database.git
cd Bible_AI_Database

# Install with API dependencies
pip install -e .[api]
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and set your API keys (optional for basic usage)
nano .env
```

**Minimal .env for testing:**
```bash
ALLOWED_ORIGINS=*
DEFAULT_RATE_LIMIT=100
```

### 3. Start API Server

```bash
# Development mode (auto-reload on code changes)
bible-api --reload

# Production mode
bible-api --host 0.0.0.0 --port 8000 --workers 4
```

**You should see:**
```
============================================================
🚀 Starting Bible AI API Server
============================================================
📍 Host: 127.0.0.1
🔌 Port: 8000
📚 Docs: http://127.0.0.1:8000/docs
============================================================

Default API Key (save this!): bible_ai_dev_key_xxxxxxxxxxxx
```

**⚠️ IMPORTANT: Save the API key printed in the console!**

---

## 📖 Test the API

### Option 1: Interactive Docs (Easiest)

1. Open browser: http://localhost:8000/docs
2. Click any endpoint (e.g., `/admin/stats`)
3. Click "Try it out"
4. Add your API key to `X-API-Key` header
5. Click "Execute"

### Option 2: cURL

```bash
# Save your API key
export API_KEY="bible_ai_dev_key_xxxxxxxxxxxx"

# Test health check (no auth required)
curl http://localhost:8000/admin/health

# Get stats (requires API key)
curl http://localhost:8000/admin/stats \
  -H "X-API-Key: $API_KEY"

# Search verses
curl http://localhost:8000/search/vector \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "love",
    "top_k": 5
  }'
```

### Option 3: Python

```python
import requests

API_KEY = "bible_ai_dev_key_xxxxxxxxxxxx"
BASE_URL = "http://localhost:8000"

# Health check
response = requests.get(f"{BASE_URL}/admin/health")
print(response.json())

# Vector search
response = requests.post(
    f"{BASE_URL}/search/vector",
    headers={"X-API-Key": API_KEY},
    json={
        "query": "God's love",
        "top_k": 5,
        "similarity_threshold": 0.3
    }
)
print(response.json())
```

---

## 🔑 API Key Management

### Create New API Key

```bash
curl -X POST http://localhost:8000/admin/keys/create \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mobile App",
    "rate_limit": 500
  }'
```

### List Keys

```bash
curl http://localhost:8000/admin/keys/list \
  -H "X-API-Key: $API_KEY"
```

---

## 📱 Mobile App Integration

### iOS (Swift)

```swift
let apiKey = "bible_ai_dev_key_xxxxxxxxxxxx"
let baseURL = "http://localhost:8000"

var request = URLRequest(url: URL(string: "\(baseURL)/search/vector")!)
request.httpMethod = "POST"
request.setValue(apiKey, forHTTPHeaderField: "X-API-Key")
request.setValue("application/json", forHTTPHeaderField: "Content-Type")

let body: [String: Any] = ["query": "faith", "top_k": 10]
request.httpBody = try? JSONSerialization.data(withJSONObject: body)

URLSession.shared.dataTask(with: request) { data, response, error in
    // Handle response
}.resume()
```

### Android (Kotlin)

```kotlin
val apiKey = "bible_ai_dev_key_xxxxxxxxxxxx"
val baseURL = "http://localhost:8000"

val request = Request.Builder()
    .url("$baseURL/search/vector")
    .addHeader("X-API-Key", apiKey)
    .post("""{"query": "faith", "top_k": 10}""".toRequestBody())
    .build()

OkHttpClient().newCall(request).execute()
```

### React Native

```javascript
const API_KEY = 'bible_ai_dev_key_xxxxxxxxxxxx';

fetch('http://localhost:8000/search/vector', {
  method: 'POST',
  headers: {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    query: 'faith',
    top_k: 10,
  }),
})
.then(response => response.json())
.then(data => console.log(data));
```

---

## 🔒 Security Notes

### For Development
- Default API key is fine for local testing
- CORS is set to `*` (allows all origins)

### For Production
1. **Generate secure API keys:**
   ```bash
   curl -X POST http://localhost:8000/admin/keys/create \
     -H "X-API-Key: $ADMIN_KEY" \
     -d '{"name": "Production", "rate_limit": 1000}'
   ```

2. **Restrict CORS in .env:**
   ```bash
   ALLOWED_ORIGINS=https://myapp.com,https://app.myapp.com
   ```

3. **Use HTTPS:**
   - Deploy behind reverse proxy (Nginx, Caddy)
   - Use SSL certificates (Let's Encrypt)

4. **Secure .env file:**
   ```bash
   chmod 600 .env  # Only owner can read/write
   ```

---

## 🐛 Troubleshooting

### "Connection refused"
- Make sure server is running: `bible-api --reload`
- Check port 8000 is not in use: `lsof -i :8000`

### "401 Unauthorized"
- Include `X-API-Key` header in request
- Use the key from server startup logs

### "429 Too Many Requests"
- You've exceeded rate limit (default: 100 req/min)
- Wait 60 seconds or create key with higher limit

### "Module not found"
- Install API dependencies: `pip install -e .[api]`

---

## 📚 Next Steps

1. **Read full documentation:** [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
2. **Explore endpoints:** http://localhost:8000/docs
3. **Customize config:** Edit `.env` file
4. **Deploy to production:** See [API_DOCUMENTATION.md#deployment](API_DOCUMENTATION.md#deployment)

---

## 🆘 Support

- **Issues:** https://github.com/ThePiousP/Bible_AI_Database/issues
- **Full Docs:** [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

---

**Happy coding! 🎉**
