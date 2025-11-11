"""
FastAPI SMS Server - Store and Display SMS Messages
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import sqlite3
from contextlib import contextmanager
import os

# Initialize FastAPI app
app = FastAPI(title="SMS Manager", description="Store and view SMS messages", version="1.0.0")

# Database configuration
DB_PATH = "sms_database.db"

# Pydantic models
class SmsMessage(BaseModel):
    address: str
    body: str
    date: int  # Timestamp in milliseconds
    read: bool = False
    type: int  # 1 = Received, 2 = Sent
    device_id: str  # Unique device identifier

class SmsResponse(BaseModel):
    id: int
    address: str
    body: str
    date: int
    read: bool
    type: int
    device_id: str
    created_at: str

class StatsResponse(BaseModel):
    total_messages: int
    unread_messages: int
    received_messages: int
    sent_messages: int

# Database context manager
@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# Initialize database
def init_db():
    """Create SMS messages table if it doesn't exist"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Create table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sms_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                address TEXT NOT NULL,
                body TEXT NOT NULL,
                date INTEGER NOT NULL,
                read BOOLEAN NOT NULL DEFAULT 0,
                type INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Check if device_id column exists
        cursor.execute("PRAGMA table_info(sms_messages)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Add device_id column if it doesn't exist (migration)
        if 'device_id' not in columns:
            print("🔧 Adding device_id column (migration)...")
            cursor.execute('''
                ALTER TABLE sms_messages 
                ADD COLUMN device_id TEXT NOT NULL DEFAULT 'unknown'
            ''')
            print("✅ device_id column added successfully!")
        
        # Create indexes for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_date ON sms_messages(date DESC)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_type ON sms_messages(type)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_read ON sms_messages(read)
        ''')
        
        # Only create device_id index if column exists
        if 'device_id' in columns or True:  # Will exist after migration
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_device_id ON sms_messages(device_id)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_address_date ON sms_messages(address, date DESC)
            ''')
        
        conn.commit()
        print("✅ Database initialized successfully!")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()
    print("✅ Database initialized successfully!")

# API Endpoints

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with SMS messages display"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SMS Manager</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            
            .header {
                background: white;
                padding: 30px;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                margin-bottom: 30px;
            }
            
            h1 {
                color: #667eea;
                font-size: 2.5em;
                margin-bottom: 10px;
            }
            
            .subtitle {
                color: #666;
                font-size: 1.1em;
            }
            
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            
            .stat-card {
                background: white;
                padding: 25px;
                border-radius: 15px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                text-align: center;
            }
            
            .stat-number {
                font-size: 3em;
                font-weight: bold;
                color: #667eea;
            }
            
            .stat-label {
                color: #666;
                font-size: 1.1em;
                margin-top: 10px;
            }
            
            .controls {
                background: white;
                padding: 20px;
                border-radius: 15px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                margin-bottom: 30px;
                display: flex;
                gap: 15px;
                flex-wrap: wrap;
                align-items: center;
            }
            
            .search-box {
                flex: 1;
                min-width: 250px;
            }
            
            .search-box input {
                width: 100%;
                padding: 12px 20px;
                border: 2px solid #e0e0e0;
                border-radius: 25px;
                font-size: 1em;
                transition: all 0.3s;
            }
            
            .search-box input:focus {
                outline: none;
                border-color: #667eea;
            }
            
            .filter-buttons {
                display: flex;
                gap: 10px;
            }
            
            .btn {
                padding: 12px 25px;
                border: none;
                border-radius: 25px;
                font-size: 1em;
                cursor: pointer;
                transition: all 0.3s;
                font-weight: 600;
            }
            
            .btn-primary {
                background: #667eea;
                color: white;
            }
            
            .btn-primary:hover {
                background: #5568d3;
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
            }
            
            .btn-secondary {
                background: #e0e0e0;
                color: #333;
            }
            
            .btn-secondary:hover {
                background: #d0d0d0;
            }
            
            .btn-secondary.active {
                background: #667eea;
                color: white;
            }
            
            .messages-container {
                background: white;
                padding: 30px;
                border-radius: 15px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            }
            
            .message-card {
                border: 2px solid #f0f0f0;
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 15px;
                transition: all 0.3s;
                cursor: pointer;
            }
            
            .message-card:hover {
                transform: translateX(5px);
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                border-color: #667eea;
            }
            
            .message-card.unread {
                background: #f0f4ff;
                border-color: #667eea;
            }
            
            .message-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
            }
            
            .message-sender {
                display: flex;
                align-items: center;
                gap: 10px;
                font-weight: 600;
                font-size: 1.1em;
                color: #333;
            }
            
            .message-icon {
                width: 35px;
                height: 35px;
                border-radius: 50%;
                background: #667eea;
                color: white;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.2em;
            }
            
            .message-icon.sent {
                background: #f093fb;
            }
            
            .message-badge {
                background: #ff6b6b;
                color: white;
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 0.8em;
                font-weight: 600;
            }
            
            .message-body {
                color: #666;
                line-height: 1.6;
                margin-bottom: 10px;
            }
            
            .message-time {
                color: #999;
                font-size: 0.9em;
            }
            
            .loading {
                text-align: center;
                padding: 50px;
                color: #667eea;
                font-size: 1.2em;
            }
            
            .empty-state {
                text-align: center;
                padding: 50px;
                color: #999;
            }
            
            .empty-state-icon {
                font-size: 4em;
                margin-bottom: 20px;
            }
            
            @media (max-width: 768px) {
                h1 {
                    font-size: 2em;
                }
                
                .controls {
                    flex-direction: column;
                }
                
                .search-box {
                    width: 100%;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📱 SMS Manager</h1>
                <p class="subtitle">View and manage all your SMS messages</p>
                <div style="margin-top: 15px;">
                    <a href="/conversations" style="
                        background: #667eea;
                        color: white;
                        padding: 10px 20px;
                        border-radius: 20px;
                        text-decoration: none;
                        font-weight: 600;
                        display: inline-block;
                    ">💬 Conversation View</a>
                </div>
            </div>
            
            <div class="stats" id="stats">
                <div class="stat-card">
                    <div class="stat-number" id="total-messages">-</div>
                    <div class="stat-label">Total Messages</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="unread-messages">-</div>
                    <div class="stat-label">Unread Messages</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="received-messages">-</div>
                    <div class="stat-label">Received</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="sent-messages">-</div>
                    <div class="stat-label">Sent</div>
                </div>
            </div>
            
            <div class="controls">
                <div class="search-box">
                    <input type="text" id="search-input" placeholder="🔍 Search messages...">
                </div>
                <div class="filter-buttons">
                    <button class="btn btn-secondary active" onclick="filterMessages('all')">All</button>
                    <button class="btn btn-secondary" onclick="filterMessages('received')">Received</button>
                    <button class="btn btn-secondary" onclick="filterMessages('sent')">Sent</button>
                    <button class="btn btn-secondary" onclick="filterMessages('unread')">Unread</button>
                </div>
                <button class="btn btn-primary" onclick="loadMessages()">🔄 Refresh</button>
            </div>
            
            <div class="messages-container">
                <div id="messages-list" class="loading">
                    Loading messages...
                </div>
            </div>
        </div>
        
        <script>
            let allMessages = [];
            let currentFilter = 'all';
            
            // Load messages on page load
            window.onload = function() {
                loadMessages();
                loadStats();
                
                // Search functionality
                document.getElementById('search-input').addEventListener('input', function(e) {
                    filterAndDisplay();
                });
            };
            
            // Load messages from API
            async function loadMessages() {
                try {
                    const response = await fetch('/api/messages');
                    allMessages = await response.json();
                    filterAndDisplay();
                } catch (error) {
                    document.getElementById('messages-list').innerHTML = 
                        '<div class="empty-state"><div class="empty-state-icon">❌</div><p>Error loading messages</p></div>';
                }
            }
            
            // Load statistics
            async function loadStats() {
                try {
                    const response = await fetch('/api/stats');
                    const stats = await response.json();
                    
                    document.getElementById('total-messages').textContent = stats.total_messages;
                    document.getElementById('unread-messages').textContent = stats.unread_messages;
                    document.getElementById('received-messages').textContent = stats.received_messages;
                    document.getElementById('sent-messages').textContent = stats.sent_messages;
                } catch (error) {
                    console.error('Error loading stats:', error);
                }
            }
            
            // Filter messages
            function filterMessages(type) {
                currentFilter = type;
                
                // Update button states
                document.querySelectorAll('.filter-buttons .btn').forEach(btn => {
                    btn.classList.remove('active');
                });
                event.target.classList.add('active');
                
                filterAndDisplay();
            }
            
            // Filter and display messages
            function filterAndDisplay() {
                let filtered = allMessages;
                
                // Apply type filter
                if (currentFilter === 'received') {
                    filtered = filtered.filter(msg => msg.type === 1);
                } else if (currentFilter === 'sent') {
                    filtered = filtered.filter(msg => msg.type === 2);
                } else if (currentFilter === 'unread') {
                    filtered = filtered.filter(msg => !msg.read);
                }
                
                // Apply search filter
                const searchTerm = document.getElementById('search-input').value.toLowerCase();
                if (searchTerm) {
                    filtered = filtered.filter(msg => 
                        msg.address.toLowerCase().includes(searchTerm) ||
                        msg.body.toLowerCase().includes(searchTerm)
                    );
                }
                
                displayMessages(filtered);
            }
            
            // Display messages in UI
            function displayMessages(messages) {
                const container = document.getElementById('messages-list');
                
                if (messages.length === 0) {
                    container.innerHTML = 
                        '<div class="empty-state"><div class="empty-state-icon">📭</div><p>No messages found</p></div>';
                    return;
                }
                
                container.innerHTML = messages.map(msg => {
                    const date = new Date(msg.date);
                    const formattedDate = date.toLocaleString();
                    const icon = msg.type === 1 ? '📧' : '➤';
                    const unreadClass = msg.read ? '' : 'unread';
                    const badge = msg.read ? '' : '<span class="message-badge">NEW</span>';
                    
                    return `
                        <div class="message-card ${unreadClass}">
                            <div class="message-header">
                                <div class="message-sender">
                                    <div class="message-icon ${msg.type === 2 ? 'sent' : ''}">${icon}</div>
                                    ${msg.address}
                                </div>
                                ${badge}
                            </div>
                            <div class="message-body">${msg.body}</div>
                            <div class="message-time">${formattedDate}</div>
                        </div>
                    `;
                }).join('');
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/api/messages", response_model=List[SmsResponse])
async def get_messages(
    limit: Optional[int] = 100,
    offset: Optional[int] = 0,
    type: Optional[int] = None,
    unread: Optional[bool] = None
):
    """Get all SMS messages with optional filters"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        query = "SELECT * FROM sms_messages WHERE 1=1"
        params = []
        
        if type is not None:
            query += " AND type = ?"
            params.append(type)
        
        if unread is not None:
            query += " AND read = ?"
            params.append(0 if unread else 1)
        
        query += " ORDER BY date DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        messages = []
        for row in rows:
            messages.append({
                "id": row["id"],
                "address": row["address"],
                "body": row["body"],
                "date": row["date"],
                "read": bool(row["read"]),
                "type": row["type"],
                "device_id": row.get("device_id", "unknown"),
                "created_at": row["created_at"]
            })
        
        return messages

@app.post("/api/messages", response_model=SmsResponse, status_code=201)
async def create_message(message: SmsMessage):
    """Store a new SMS message"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO sms_messages (address, body, date, read, type, device_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (message.address, message.body, message.date, message.read, message.type, message.device_id))
        
        conn.commit()
        message_id = cursor.lastrowid
        
        # Fetch the created message
        cursor.execute("SELECT * FROM sms_messages WHERE id = ?", (message_id,))
        row = cursor.fetchone()
        
        return {
            "id": row["id"],
            "address": row["address"],
            "body": row["body"],
            "date": row["date"],
            "read": bool(row["read"]),
            "type": row["type"],
            "device_id": row.get("device_id", "unknown"),
            "created_at": row["created_at"]
        }

@app.post("/api/messages/bulk", status_code=201)
async def create_messages_bulk(messages: List[SmsMessage]):
    """Store multiple SMS messages at once"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        data = [(msg.address, msg.body, msg.date, msg.read, msg.type, msg.device_id) for msg in messages]
        
        cursor.executemany('''
            INSERT INTO sms_messages (address, body, date, read, type, device_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', data)
        
        conn.commit()
        
        return {"message": f"Successfully stored {len(messages)} messages", "count": len(messages)}

@app.get("/api/messages/{message_id}", response_model=SmsResponse)
async def get_message(message_id: int):
    """Get a specific message by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sms_messages WHERE id = ?", (message_id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Message not found")
        
        return {
            "id": row["id"],
            "address": row["address"],
            "body": row["body"],
            "date": row["date"],
            "read": bool(row["read"]),
            "type": row["type"],
            "device_id": row.get("device_id", "unknown"),
            "created_at": row["created_at"]
        }

@app.delete("/api/messages/{message_id}")
async def delete_message(message_id: int):
    """Delete a specific message"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sms_messages WHERE id = ?", (message_id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Message not found")
        
        return {"message": "Message deleted successfully"}

@app.get("/api/stats", response_model=StatsResponse)
async def get_statistics():
    """Get SMS statistics"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Total messages
        cursor.execute("SELECT COUNT(*) as count FROM sms_messages")
        total = cursor.fetchone()["count"]
        
        # Unread messages
        cursor.execute("SELECT COUNT(*) as count FROM sms_messages WHERE read = 0")
        unread = cursor.fetchone()["count"]
        
        # Received messages
        cursor.execute("SELECT COUNT(*) as count FROM sms_messages WHERE type = 1")
        received = cursor.fetchone()["count"]
        
        # Sent messages
        cursor.execute("SELECT COUNT(*) as count FROM sms_messages WHERE type = 2")
        sent = cursor.fetchone()["count"]
        
        return {
            "total_messages": total,
            "unread_messages": unread,
            "received_messages": received,
            "sent_messages": sent
        }

@app.delete("/api/messages")
async def delete_all_messages():
    """Delete all messages (use with caution!)"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sms_messages")
        conn.commit()
        
        return {"message": "All messages deleted successfully", "count": cursor.rowcount}

@app.get("/api/conversations")
async def get_conversations():
    """Get all unique conversations grouped by address"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get unique addresses with latest message info
        cursor.execute('''
            SELECT 
                address,
                MAX(date) as last_message_date,
                COUNT(*) as message_count,
                SUM(CASE WHEN read = 0 THEN 1 ELSE 0 END) as unread_count
            FROM sms_messages
            GROUP BY address
            ORDER BY last_message_date DESC
        ''')
        
        conversations = []
        for row in cursor.fetchall():
            conversations.append({
                "address": row["address"],
                "last_message_date": row["last_message_date"],
                "message_count": row["message_count"],
                "unread_count": row["unread_count"]
            })
        
        return conversations

@app.get("/api/conversation/{address}")
async def get_conversation(address: str):
    """Get all messages for a specific address (conversation view)"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM sms_messages 
            WHERE address = ? 
            ORDER BY date ASC
        ''', (address,))
        
        rows = cursor.fetchall()
        
        messages = []
        for row in rows:
            messages.append({
                "id": row["id"],
                "address": row["address"],
                "body": row["body"],
                "date": row["date"],
                "read": bool(row["read"]),
                "type": row["type"],
                "device_id": row.get("device_id", "unknown"),
                "created_at": row["created_at"]
            })
        
        return messages

@app.get("/conversations", response_class=HTMLResponse)
async def conversations_page():
    """Conversation view page (like messaging app)"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SMS Conversations</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: #f5f5f5;
                height: 100vh;
                overflow: hidden;
            }
            
            .container {
                display: flex;
                height: 100vh;
                max-width: 1400px;
                margin: 0 auto;
                background: white;
                box-shadow: 0 0 20px rgba(0,0,0,0.1);
            }
            
            /* Conversation List (Left Panel) */
            .conversation-list {
                width: 350px;
                border-right: 1px solid #e0e0e0;
                display: flex;
                flex-direction: column;
                background: #fafafa;
            }
            
            .conversation-header {
                padding: 20px;
                background: #667eea;
                color: white;
            }
            
            .conversation-header h1 {
                font-size: 1.5em;
                margin-bottom: 5px;
            }
            
            .search-bar {
                padding: 15px;
                background: white;
                border-bottom: 1px solid #e0e0e0;
            }
            
            .search-bar input {
                width: 100%;
                padding: 10px 15px;
                border: 1px solid #e0e0e0;
                border-radius: 20px;
                font-size: 0.9em;
            }
            
            .conversation-items {
                flex: 1;
                overflow-y: auto;
            }
            
            .conversation-item {
                padding: 15px 20px;
                border-bottom: 1px solid #e0e0e0;
                cursor: pointer;
                transition: background 0.2s;
            }
            
            .conversation-item:hover {
                background: #f0f0f0;
            }
            
            .conversation-item.active {
                background: #e8ecff;
                border-left: 3px solid #667eea;
            }
            
            .conversation-item.unread {
                background: #f0f4ff;
                font-weight: 600;
            }
            
            .conversation-name {
                font-weight: 600;
                font-size: 1em;
                margin-bottom: 5px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .conversation-preview {
                color: #666;
                font-size: 0.9em;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            
            .conversation-time {
                color: #999;
                font-size: 0.8em;
            }
            
            .unread-badge {
                background: #667eea;
                color: white;
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 0.75em;
                font-weight: 600;
            }
            
            /* Messages Panel (Right Panel) */
            .messages-panel {
                flex: 1;
                display: flex;
                flex-direction: column;
                background: #f9f9f9;
            }
            
            .messages-header {
                padding: 20px;
                background: white;
                border-bottom: 1px solid #e0e0e0;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .messages-header h2 {
                font-size: 1.2em;
                color: #333;
            }
            
            .device-badge {
                background: #e0e0e0;
                padding: 5px 15px;
                border-radius: 15px;
                font-size: 0.85em;
                color: #666;
            }
            
            .messages-content {
                flex: 1;
                overflow-y: auto;
                padding: 20px;
            }
            
            .message-group {
                display: flex;
                margin-bottom: 15px;
            }
            
            .message-group.sent {
                justify-content: flex-end;
            }
            
            .message-bubble {
                max-width: 60%;
                padding: 12px 16px;
                border-radius: 18px;
                position: relative;
            }
            
            .message-bubble.received {
                background: white;
                border: 1px solid #e0e0e0;
                color: #333;
                border-bottom-left-radius: 4px;
            }
            
            .message-bubble.sent {
                background: #667eea;
                color: white;
                border-bottom-right-radius: 4px;
            }
            
            .message-text {
                line-height: 1.4;
                word-wrap: break-word;
            }
            
            .message-time {
                font-size: 0.75em;
                margin-top: 5px;
                opacity: 0.7;
            }
            
            .empty-state {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100%;
                color: #999;
            }
            
            .empty-state-icon {
                font-size: 4em;
                margin-bottom: 10px;
            }
            
            @media (max-width: 768px) {
                .conversation-list {
                    width: 100%;
                }
                
                .messages-panel {
                    display: none;
                }
                
                .conversation-list.hidden {
                    display: none;
                }
                
                .messages-panel.visible {
                    display: flex;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <!-- Conversation List -->
            <div class="conversation-list">
                <div class="conversation-header">
                    <h1>💬 Messages</h1>
                    <p style="font-size: 0.9em; opacity: 0.9;">Conversation View</p>
                </div>
                
                <div class="search-bar">
                    <input type="text" id="search-conv" placeholder="🔍 Search conversations...">
                </div>
                
                <div class="conversation-items" id="conversations-list">
                    <div class="empty-state">
                        <div class="empty-state-icon">💬</div>
                        <p>Loading conversations...</p>
                    </div>
                </div>
            </div>
            
            <!-- Messages Panel -->
            <div class="messages-panel">
                <div class="messages-header">
                    <h2 id="conversation-title">Select a conversation</h2>
                    <span class="device-badge" id="device-badge"></span>
                </div>
                
                <div class="messages-content" id="messages-content">
                    <div class="empty-state">
                        <div class="empty-state-icon">📱</div>
                        <p>Select a conversation to view messages</p>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            let conversations = [];
            let currentConversation = null;
            
            window.onload = function() {
                loadConversations();
                
                document.getElementById('search-conv').addEventListener('input', function(e) {
                    filterConversations(e.target.value);
                });
            };
            
            async function loadConversations() {
                try {
                    const response = await fetch('/api/conversations');
                    conversations = await response.json();
                    displayConversations(conversations);
                } catch (error) {
                    console.error('Error loading conversations:', error);
                }
            }
            
            function displayConversations(convs) {
                const container = document.getElementById('conversations-list');
                
                if (convs.length === 0) {
                    container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📭</div><p>No conversations</p></div>';
                    return;
                }
                
                container.innerHTML = convs.map(conv => {
                    const date = new Date(conv.last_message_date);
                    const timeStr = formatTime(date);
                    const unreadBadge = conv.unread_count > 0 ? 
                        `<span class="unread-badge">${conv.unread_count}</span>` : '';
                    const unreadClass = conv.unread_count > 0 ? 'unread' : '';
                    
                    return `
                        <div class="conversation-item ${unreadClass}" onclick="loadConversation('${conv.address}')">
                            <div class="conversation-name">
                                <span>${conv.address}</span>
                                ${unreadBadge}
                            </div>
                            <div class="conversation-preview">${conv.message_count} messages</div>
                            <div class="conversation-time">${timeStr}</div>
                        </div>
                    `;
                }).join('');
            }
            
            async function loadConversation(address) {
                currentConversation = address;
                
                // Update active state
                document.querySelectorAll('.conversation-item').forEach(item => {
                    item.classList.remove('active');
                });
                event.target.closest('.conversation-item').classList.add('active');
                
                // Load messages
                try {
                    const response = await fetch(`/api/conversation/${encodeURIComponent(address)}`);
                    const messages = await response.json();
                    displayMessages(messages, address);
                } catch (error) {
                    console.error('Error loading conversation:', error);
                }
            }
            
            function displayMessages(messages, address) {
                const container = document.getElementById('messages-content');
                const titleEl = document.getElementById('conversation-title');
                const deviceBadge = document.getElementById('device-badge');
                
                titleEl.textContent = address;
                
                if (messages.length > 0 && messages[0].device_id) {
                    deviceBadge.textContent = `📱 ${messages[0].device_id}`;
                    deviceBadge.style.display = 'inline-block';
                } else {
                    deviceBadge.style.display = 'none';
                }
                
                if (messages.length === 0) {
                    container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📭</div><p>No messages</p></div>';
                    return;
                }
                
                container.innerHTML = messages.map(msg => {
                    const date = new Date(msg.date);
                    const timeStr = date.toLocaleString();
                    const messageClass = msg.type === 2 ? 'sent' : 'received';
                    const bubbleClass = msg.type === 2 ? 'sent' : 'received';
                    
                    return `
                        <div class="message-group ${messageClass}">
                            <div class="message-bubble ${bubbleClass}">
                                <div class="message-text">${msg.body}</div>
                                <div class="message-time">${timeStr}</div>
                            </div>
                        </div>
                    `;
                }).join('');
                
                // Scroll to bottom
                container.scrollTop = container.scrollHeight;
            }
            
            function filterConversations(query) {
                const filtered = conversations.filter(conv => 
                    conv.address.toLowerCase().includes(query.toLowerCase())
                );
                displayConversations(filtered);
            }
            
            function formatTime(date) {
                const now = new Date();
                const diffMs = now - date;
                const diffMins = Math.floor(diffMs / 60000);
                const diffHours = Math.floor(diffMs / 3600000);
                const diffDays = Math.floor(diffMs / 86400000);
                
                if (diffMins < 1) return 'Just now';
                if (diffMins < 60) return `${diffMins}m ago`;
                if (diffHours < 24) return `${diffHours}h ago`;
                if (diffDays < 7) return `${diffDays}d ago`;
                return date.toLocaleDateString();
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

