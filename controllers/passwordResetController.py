from database.database import users_collection
from models import PasswordResetRequest, PasswordResetConfirm
from utils.hash_password import hash_password

async def verify_reset_request(reset_request: PasswordResetRequest):
    # Check if user exists with matching email and username
    user = users_collection.find_one({
        "email": reset_request.email,
        "username": reset_request.username
    })
    
    if not user:
        return {
            "status": 404,
            "error": "No account found with this email and username combination"
        }
    
    return {
        "status": 200,
        "message": "Account verified. Please proceed with password reset"
    }

async def update_password(reset_confirm: PasswordResetConfirm):
    # Find user by email
    user = users_collection.find_one({"email": reset_confirm.email})
    
    if not user:
        return {
            "status": 404,
            "error": "Account not found"
        }
    
    # Hash the new password
    hashed_password = hash_password(reset_confirm.new_password)
    
    # Update the password
    result = users_collection.update_one(
        {"email": reset_confirm.email},
        {"$set": {"password": hashed_password}}
    )
    
    if result.modified_count == 0:
        return {
            "status": 500,
            "error": "Failed to update password"
        }
    
    return {
        "status": 200,
        "message": "Password updated successfully"
    }
