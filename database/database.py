from pymongo import MongoClient
from config import MONGO_URI

client = MongoClient(MONGO_URI)
db = client.chinni_ai_db

# Collections
users_collection = db.users
messages_collection = db.messages
alarms_collection = db.alarms
tasks_collection = db.tasks

# Create indexes for better query performance
def setup_indexes():
    alarms_collection.create_index([("user_id", 1), ("alarm_time", 1)])
    tasks_collection.create_index([("user_id", 1), ("due_date", 1)])
