# 📱 FastAPI SMS Manager

A complete FastAPI application to store and display SMS messages with a beautiful web UI.

## ✨ Features

- ✅ **Store SMS messages** in SQLite database
- ✅ **Beautiful web UI** to view all messages
- ✅ **Real-time statistics** (total, unread, received, sent)
- ✅ **Search functionality** (search by sender or message content)
- ✅ **Filter messages** (All, Received, Sent, Unread)
- ✅ **REST API** for integration with Android app
- ✅ **Bulk upload** support
- ✅ **Responsive design** (works on mobile and desktop)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd fastapi_sms_server
pip install -r requirements.txt
```

### 2. Run the Server

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Open in Browser

```
http://localhost:8000
```

## 📚 API Documentation

FastAPI provides automatic interactive documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔌 API Endpoints

### 1. Get All Messages

```http
GET /api/messages?limit=100&offset=0
```

**Query Parameters:**
- `limit` (optional): Number of messages to return (default: 100)
- `offset` (optional): Number of messages to skip (default: 0)
- `type` (optional): Filter by type (1=Received, 2=Sent)
- `unread` (optional): Filter by read status (true/false)

**Response:**
```json
[
  {
    "id": 1,
    "address": "+1234567890",
    "body": "Hello, this is a test message!",
    "date": 1699721645000,
    "read": false,
    "type": 1,
    "created_at": "2024-11-11 12:30:45"
  }
]
```

### 2. Create Single Message

```http
POST /api/messages
Content-Type: application/json

{
  "address": "+1234567890",
  "body": "Hello World!",
  "date": 1699721645000,
  "read": false,
  "type": 1
}
```

### 3. Create Multiple Messages (Bulk)

```http
POST /api/messages/bulk
Content-Type: application/json

[
  {
    "address": "+1234567890",
    "body": "Message 1",
    "date": 1699721645000,
    "read": false,
    "type": 1
  },
  {
    "address": "+9876543210",
    "body": "Message 2",
    "date": 1699721646000,
    "read": true,
    "type": 2
  }
]
```

### 4. Get Single Message

```http
GET /api/messages/{message_id}
```

### 5. Delete Message

```http
DELETE /api/messages/{message_id}
```

### 6. Get Statistics

```http
GET /api/stats
```

**Response:**
```json
{
  "total_messages": 150,
  "unread_messages": 23,
  "received_messages": 95,
  "sent_messages": 55
}
```

### 7. Delete All Messages

```http
DELETE /api/messages
```

## 📱 Integration with Android App

### Send Messages from Android

Add this code to your Android app to send SMS messages to the server:

```kotlin
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.*

// Define API interface
interface SmsApi {
    @POST("api/messages")
    suspend fun sendMessage(@Body message: SmsMessageDto): Response<SmsResponse>
    
    @POST("api/messages/bulk")
    suspend fun sendMessagesBulk(@Body messages: List<SmsMessageDto>): Response<BulkResponse>
}

data class SmsMessageDto(
    val address: String,
    val body: String,
    val date: Long,
    val read: Boolean,
    val type: Int
)

// Create Retrofit instance
val retrofit = Retrofit.Builder()
    .baseUrl("http://YOUR_SERVER_IP:8000/")
    .addConverterFactory(GsonConverterFactory.create())
    .build()

val api = retrofit.create(SmsApi::class.java)

// Send messages
suspend fun uploadSmsMessages() {
    val smsInboxManager = SmsInboxManager(context)
    val messages = smsInboxManager.getAllMessages()
    
    val messageDtos = messages.map { msg ->
        SmsMessageDto(
            address = msg.address,
            body = msg.body,
            date = msg.date,
            read = msg.read,
            type = msg.type
        )
    }
    
    try {
        val response = api.sendMessagesBulk(messageDtos)
        if (response.isSuccessful) {
            println("✅ Uploaded ${messages.size} messages!")
        }
    } catch (e: Exception) {
        println("❌ Error: ${e.message}")
    }
}
```

## 🎨 Web UI Features

### Home Page

- **Statistics Dashboard**: Shows total, unread, received, and sent message counts
- **Search Bar**: Search messages by sender or content
- **Filter Buttons**: Filter by All, Received, Sent, or Unread
- **Refresh Button**: Reload messages from database
- **Message Cards**: Beautiful cards showing:
  - Sender phone number
  - Message body
  - Timestamp
  - Read/Unread status (NEW badge)
  - Message direction (📧 received, ➤ sent)

## 🗄️ Database Schema

```sql
CREATE TABLE sms_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    address TEXT NOT NULL,
    body TEXT NOT NULL,
    date INTEGER NOT NULL,
    read BOOLEAN NOT NULL DEFAULT 0,
    type INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_date ON sms_messages(date DESC);
CREATE INDEX idx_type ON sms_messages(type);
CREATE INDEX idx_read ON sms_messages(read);
```

## 🧪 Testing with cURL

### Add a test message

```bash
curl -X POST http://localhost:8000/api/messages \
  -H "Content-Type: application/json" \
  -d '{
    "address": "+1234567890",
    "body": "This is a test message from cURL!",
    "date": 1699721645000,
    "read": false,
    "type": 1
  }'
```

### Get all messages

```bash
curl http://localhost:8000/api/messages
```

### Get statistics

```bash
curl http://localhost:8000/api/stats
```

### Add multiple messages

```bash
curl -X POST http://localhost:8000/api/messages/bulk \
  -H "Content-Type: application/json" \
  -d '[
    {
      "address": "+1111111111",
      "body": "Message 1",
      "date": 1699721645000,
      "read": false,
      "type": 1
    },
    {
      "address": "+2222222222",
      "body": "Message 2",
      "date": 1699721646000,
      "read": true,
      "type": 2
    }
  ]'
```

## 🐍 Testing with Python

```python
import requests

BASE_URL = "http://localhost:8000"

# Add a message
message = {
    "address": "+1234567890",
    "body": "Hello from Python!",
    "date": 1699721645000,
    "read": False,
    "type": 1
}

response = requests.post(f"{BASE_URL}/api/messages", json=message)
print(response.json())

# Get all messages
response = requests.get(f"{BASE_URL}/api/messages")
messages = response.json()
print(f"Total messages: {len(messages)}")

# Get statistics
response = requests.get(f"{BASE_URL}/api/stats")
stats = response.json()
print(f"Stats: {stats}")
```

## 📦 Project Structure

```
fastapi_sms_server/
├── main.py              # Main FastAPI application
├── requirements.txt     # Python dependencies
├── README.md           # This file
└── sms_database.db     # SQLite database (created automatically)
```

## 🔒 Security Notes

For production deployment:

1. **Add authentication** (OAuth2, JWT tokens)
2. **Use HTTPS** (SSL/TLS certificates)
3. **Add rate limiting** (to prevent abuse)
4. **Validate input** (already done with Pydantic)
5. **Use environment variables** for configuration
6. **Add CORS** if needed for frontend apps

Example adding CORS:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🚀 Deployment

### Deploy to Production Server

```bash
# Install dependencies
pip install -r requirements.txt

# Run with gunicorn (production server)
pip install gunicorn
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Deploy with Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📊 Performance

- SQLite with indexes for fast queries
- Pagination support (limit/offset)
- Efficient bulk insert operations
- Lightweight and fast

## 🎉 Features to Add

- [ ] User authentication
- [ ] Message threading/conversations
- [ ] Export to CSV/JSON
- [ ] Message analytics (charts, graphs)
- [ ] Real-time updates (WebSockets)
- [ ] Contact name resolution
- [ ] Backup and restore

## 📝 License

MIT License - Feel free to use and modify!

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

---

**Happy SMS Managing!** 📱✨

