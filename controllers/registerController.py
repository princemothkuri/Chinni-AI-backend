from database.database import users_collection
from datetime import datetime
from utils.hash_password import hash_password


def save_user_to_database(user):
    try:
        # Check if username or email already exists
        existing_user = users_collection.find_one({
            "$or": [
                {"username": user.username},
                {"email": user.email}
            ]
        })
        
        if existing_user:
            if existing_user["username"] == user.username:
                return {"error": "Username already exists", "status": 400}
            else:
                return {"error": "Email already exists", "status": 400}
        
        # Prepare user data for database
        user_data = {
            "firstName": user.firstName,
            "lastName": user.lastName,
            "username": user.username,
            "email": user.email,
            "password": hash_password(user.password),
            "created_at": datetime.utcnow()
        }
        
        # Insert user into database
        users_collection.insert_one(user_data)
        return {"message": "User registered successfully", "status": 201}
    
    except Exception as e:
        return {"error": "An unexpected error occurred", "status": 500}
