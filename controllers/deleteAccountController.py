from bson import ObjectId
from database.database import users_collection, alarms_collection, messages_collection, tasks_collection

def delete_user_account(user_id):
    try:
        # Delete user from users collection
        users_result = users_collection.delete_one({"_id": ObjectId(user_id)})
        
        # Delete user's alarms
        alarms_collection.delete_many({"user_id": ObjectId(user_id)})
        
        # Delete user's messages
        messages_collection.delete_many({"user_id": ObjectId(user_id)})
        
        # Delete user's tasks
        tasks_collection.delete_many({"user_id": ObjectId(user_id)})
        
        if users_result.deleted_count == 1:
            return {"message": "Account and all related data deleted successfully", "status": 200}
        else:
            return {"error": "Failed to delete account", "status": 500}
    
    except Exception as e:
        return {"error": "An unexpected error occurred", "status": 500}