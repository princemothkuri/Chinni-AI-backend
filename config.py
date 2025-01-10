import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
FRONTEND_URL = os.getenv("FRONTEND_URL")
