from bson import ObjectId
from database.database import users_collection

def update_user_profile(user_id, profile_data):
    try:
        # Check if the email or username already exists for another user
        existing_user = users_collection.find_one(
            {
                "$or": [
                    {"email": profile_data.get("email")},
                    {"username": profile_data.get("username")}
                ],
                "_id": {"$ne": ObjectId(user_id)}
            },
            {"email": 1, "username": 1}
        )

        if existing_user:
            if existing_user.get("email") == profile_data.get("email"):   
                return {"error": "Email is already in use, please use a different email", "status": 400}
            if existing_user.get("username") == profile_data.get("username"):
                return {"error": "Username is already in use, please use a different Username", "status": 400}

        # Update user's profile in the database
        result = users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": profile_data}
        )
        
        if result.modified_count == 1:
            return {"message": "Profile updated successfully", "status": 200}
        else:
            return {"error": "Failed to update profile", "status": 500}
    
    except Exception as e:
        return {"error": "An unexpected error occurred", "status": 500}


