import bcrypt
import jwt
import time
from datetime import datetime, timedelta
from core.db import get_db
from config import JWT_SECRET, SESSION_TIMEOUT

def hash_password(password):
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(password, hashed):
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def create_user(username, email, password):
    """Create a new user account"""
    db = get_db()
    
    # Check if user already exists
    existing_user = db.users.find_one({
        "$or": [
            {"username": username},
            {"email": email}
        ]
    })
    
    if existing_user:
        if existing_user["username"] == username:
            return False, "Username already exists"
        else:
            return False, "Email already exists"
    
    # Create new user
    user = {
        "username": username,
        "email": email,
        "password_hash": hash_password(password),
        "created_at": datetime.utcnow(),
        "last_login": None
    }
    
    db.users.insert_one(user)
    return True, "User created successfully"

def authenticate_user(username, password):
    """Authenticate user and return user data if successful"""
    db = get_db()
    
    user = db.users.find_one({"username": username})
    if not user:
        return None, "Invalid username or password"
    
    if not verify_password(password, user["password_hash"]):
        return None, "Invalid username or password"
    
    # Update last login
    db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"last_login": datetime.utcnow()}}
    )
    
    # Remove password hash from user data
    user.pop("password_hash", None)
    return user, "Login successful"

def create_session_token(user_id, username):
    """Create a JWT session token"""
    payload = {
        "user_id": str(user_id),
        "username": username,
        "exp": datetime.utcnow() + timedelta(seconds=SESSION_TIMEOUT),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def verify_session_token(token):
    """Verify and decode a JWT session token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def get_user_by_id(user_id):
    """Get user data by ID"""
    db = get_db()
    user = db.users.find_one({"_id": user_id})
    if user:
        user.pop("password_hash", None)
    return user 