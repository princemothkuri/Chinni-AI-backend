from bson import ObjectId
from database.database import users_collection

def save_api_key_to_database(user_id, apikey):
    try:        
        # Update user's API key in the database
        result = users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"api_key": apikey}}
        )
        
        if result.modified_count == 1:
            return {"message": "API key saved successfully", "status": 201}
        else:
            return {"error": "Failed to save API key", "status": 500}
    
    except Exception as e:
        return {"error": "An unexpected error occurred", "status": 500}

def get_api_key_from_database(user_id):
    try:
        # Retrieve user's API key from the database
        user = users_collection.find_one({"_id": ObjectId(user_id)}, {"api_key": 1})
        
        if user and "api_key" in user:
            return {"api_key": user["api_key"], "status": 200}
        else:
            return {"error": "API key not found", "status": 404}
    
    except Exception as e:
        return {"error": "An unexpected error occurred", "status": 500}
