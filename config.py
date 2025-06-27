import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "semantic_grader"
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
SESSION_TIMEOUT = 3600  # 1 hour in seconds
