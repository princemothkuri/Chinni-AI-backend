from database.database import users_collection
from utils.hash_password import verify_password
from utils.jwt_handler import create_access_token

def verify_login(credentials):
    try:
        # Check if user exists with either username or email
        user = users_collection.find_one({
            "$or": [
                {"username": credentials.usernameOrEmail},
                {"email": credentials.usernameOrEmail}
            ]
        })

        if not user:
            return {
                "error": "Invalid username/email or password",
                "status": 401
            }

        # Verify password
        if not verify_password(credentials.password, user["password"]):
            return {
                "error": "Invalid username/email or password",
                "status": 401
            }

        # Generate JWT token
        token = create_access_token({
            "user_id": str(user["_id"]),
            "firstName": user["firstName"],
            "lastName": user["lastName"],
            "username": user["username"],
            "email": user["email"]
        })

        return {
            "message": "Login successful",
            "token": token,
            "status": 200
        }

    except Exception as e:
        return {
            "error": "An unexpected error occurred",
            "status": 500
        }