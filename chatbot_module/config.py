import os
from dotenv import load_dotenv

load_dotenv()

# PostgreSQL URI
DATABASE_URI = os.getenv("DATABASE_URI", "postgres://ml_user:ml_password@localhost:5432/ml_db")

# OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Max chats per user
MAX_CHATS_PER_USER = int(os.getenv("MAX_CHATS_PER_USER", 5))
