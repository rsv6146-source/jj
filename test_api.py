"""
Test script for SMS API
Run this to populate the database with test data
"""
import requests
import time

BASE_URL = "http://localhost:8000"

# Test data
test_messages = [
    {
        "address": "+1234567890",
        "body": "Hey! How are you doing?",
        "date": int(time.time() * 1000) - 3600000,  # 1 hour ago
        "read": True,
        "type": 1
    },
    {
        "address": "+9876543210",
        "body": "I'm good! Just finished a workout.",
        "date": int(time.time() * 1000) - 3000000,  # 50 minutes ago
        "read": True,
        "type": 2
    },
    {
        "address": "+1234567890",
        "body": "That's great! What did you do?",
        "date": int(time.time() * 1000) - 2400000,  # 40 minutes ago
        "read": True,
        "type": 1
    },
    {
        "address": "+5555555555",
        "body": "Your verification code is 123456. Do not share this code with anyone.",
        "date": int(time.time() * 1000) - 1800000,  # 30 minutes ago
        "read": False,
        "type": 1
    },
    {
        "address": "+1111111111",
        "body": "Reminder: Your appointment is tomorrow at 3 PM.",
        "date": int(time.time() * 1000) - 900000,  # 15 minutes ago
        "read": False,
        "type": 1
    },
    {
        "address": "Mom",
        "body": "Don't forget to buy milk on your way home!",
        "date": int(time.time() * 1000) - 600000,  # 10 minutes ago
        "read": False,
        "type": 1
    },
    {
        "address": "Mom",
        "body": "Okay, I'll get it!",
        "date": int(time.time() * 1000) - 300000,  # 5 minutes ago
        "read": True,
        "type": 2
    },
    {
        "address": "+7777777777",
        "body": "🎉 Congratulations! You've won a prize. Click here to claim: http://fake-link.com",
        "date": int(time.time() * 1000) - 120000,  # 2 minutes ago
        "read": False,
        "type": 1
    },
    {
        "address": "Boss",
        "body": "Can you send me the report by end of day?",
        "date": int(time.time() * 1000) - 60000,  # 1 minute ago
        "read": False,
        "type": 1
    },
    {
        "address": "+2222222222",
        "body": "Hey, want to grab lunch today?",
        "date": int(time.time() * 1000),  # Just now
        "read": False,
        "type": 1
    }
]

def test_bulk_upload():
    """Test bulk upload endpoint"""
    print("📤 Uploading test messages...")
    
    try:
        response = requests.post(f"{BASE_URL}/api/messages/bulk", json=test_messages)
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Successfully uploaded {result['count']} messages!")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def test_get_messages():
    """Test get messages endpoint"""
    print("\n📥 Fetching messages...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/messages")
        
        if response.status_code == 200:
            messages = response.json()
            print(f"✅ Retrieved {len(messages)} messages")
            
            # Display first 3 messages
            print("\n📱 Sample messages:")
            for msg in messages[:3]:
                print(f"  • {msg['address']}: {msg['body'][:50]}...")
            
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def test_get_stats():
    """Test statistics endpoint"""
    print("\n📊 Fetching statistics...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/stats")
        
        if response.status_code == 200:
            stats = response.json()
            print("✅ Statistics:")
            print(f"  • Total messages: {stats['total_messages']}")
            print(f"  • Unread messages: {stats['unread_messages']}")
            print(f"  • Received: {stats['received_messages']}")
            print(f"  • Sent: {stats['sent_messages']}")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def test_filter_unread():
    """Test filtering unread messages"""
    print("\n🔍 Fetching unread messages...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/messages?unread=true")
        
        if response.status_code == 200:
            messages = response.json()
            print(f"✅ Found {len(messages)} unread messages")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def test_filter_received():
    """Test filtering received messages"""
    print("\n📥 Fetching received messages...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/messages?type=1")
        
        if response.status_code == 200:
            messages = response.json()
            print(f"✅ Found {len(messages)} received messages")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing FastAPI SMS Server")
    print("=" * 50)
    
    # Check if server is running
    try:
        requests.get(BASE_URL)
        print("✅ Server is running!\n")
    except:
        print("❌ Error: Server is not running!")
        print("Please start the server with: python main.py")
        exit(1)
    
    # Run tests
    success = all([
        test_bulk_upload(),
        test_get_messages(),
        test_get_stats(),
        test_filter_unread(),
        test_filter_received()
    ])
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All tests passed!")
        print(f"\n🌐 Open browser: {BASE_URL}")
    else:
        print("❌ Some tests failed!")

