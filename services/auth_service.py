import bcrypt
import jwt
import time
from datetime import datetime, timedelta
from core.db import get_db
from config import JWT_SECRET, SESSION_TIMEOUT

def hash_password(password):
    """Hash a password using bcrypt"""
    try:
        if not password or not isinstance(password, str):
            return None
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    except Exception as e:
        print(f"Error hashing password: {e}")
        return None

def verify_password(password, hashed):
    """Verify a password against its hash"""
    try:
        if not password or not hashed:
            return False
        return bcrypt.checkpw(password.encode('utf-8'), hashed)
    except Exception as e:
        print(f"Error verifying password: {e}")
        return False

def create_user(username, email, password):
    """Create a new user account"""
    try:
        db = get_db()
        
        # Validate inputs
        if not username or len(username) < 3:
            return False, "Username must be at least 3 characters long"
        
        if not email or "@" not in email:
            return False, "Please enter a valid email address"
        
        if not password or len(password) < 6:
            return False, "Password must be at least 6 characters long"
        
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
        
        # Hash password
        password_hash = hash_password(password)
        if not password_hash:
            return False, "Error processing password"
        
        # Create new user
        user = {
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "created_at": datetime.utcnow(),
            "last_login": None
        }
        
        result = db.users.insert_one(user)
        if result.inserted_id:
            return True, "User created successfully"
        else:
            return False, "Failed to create user"
            
    except Exception as e:
        print(f"Error creating user: {e}")
        return False, f"Error creating user: {str(e)}"

def authenticate_user(username, password):
    """Authenticate user and return user data if successful"""
    try:
        db = get_db()
        
        # Validate inputs
        if not username or not password:
            return None, "Username and password are required"
        
        user = db.users.find_one({"username": username})
        if not user:
            return None, "Invalid username or password"
        
        if not verify_password(password, user["password_hash"]):
            return None, "Invalid username or password"
        
        # Update last login
        try:
            db.users.update_one(
                {"_id": user["_id"]},
                {"$set": {"last_login": datetime.utcnow()}}
            )
        except Exception as e:
            print(f"Warning: Could not update last login: {e}")
        
        # Remove password hash from user data
        user.pop("password_hash", None)
        return user, "Login successful"
        
    except Exception as e:
        print(f"Error authenticating user: {e}")
        return None, f"Authentication error: {str(e)}"

def create_session_token(user_id, username):
    """Create a JWT session token"""
    try:
        if not user_id or not username:
            return None
        
        payload = {
            "user_id": str(user_id),
            "username": username,
            "exp": datetime.utcnow() + timedelta(seconds=SESSION_TIMEOUT),
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    except Exception as e:
        print(f"Error creating session token: {e}")
        return None

def verify_session_token(token):
    """Verify and decode a JWT session token"""
    try:
        if not token:
            return None
        
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception as e:
        print(f"Error verifying session token: {e}")
        return None

def get_user_by_id(user_id):
    """Get user data by ID"""
    try:
        if not user_id:
            return None
        
        db = get_db()
        user = db.users.find_one({"_id": user_id})
        if user:
            user.pop("password_hash", None)
        return user
    except Exception as e:
        print(f"Error getting user by ID: {e}")
        return None

def refresh_session_token(token):
    """Refresh a session token if it's still valid"""
    try:
        if not token:
            return None
        
        # Decode the token without checking expiration
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"], options={"verify_exp": False})
        
        # Check if token is within refresh window (e.g., 5 minutes before expiry)
        exp_timestamp = payload.get('exp')
        if exp_timestamp:
            current_time = datetime.utcnow().timestamp()
            time_until_expiry = exp_timestamp - current_time
            
            # If token expires in more than 5 minutes, refresh it
            if time_until_expiry > 300:  # 5 minutes
                return create_session_token(payload['user_id'], payload['username'])
        
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception as e:
        print(f"Error refreshing session token: {e}")
        return None

def get_session_info(token):
    """Get session information without verifying expiration"""
    try:
        if not token:
            return None
        
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"], options={"verify_exp": False})
        return {
            "user_id": payload.get('user_id'),
            "username": payload.get('username'),
            "expires_at": payload.get('exp'),
            "issued_at": payload.get('iat'),
            "is_expired": datetime.utcnow().timestamp() > payload.get('exp', 0) if payload.get('exp') else True
        }
    except jwt.InvalidTokenError:
        return None
    except Exception as e:
        print(f"Error getting session info: {e}")
        return None 