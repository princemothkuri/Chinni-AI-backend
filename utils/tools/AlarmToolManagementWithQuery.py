from langchain.tools import BaseTool
from typing import Optional, Literal, Type
from pydantic import BaseModel, Field
from datetime import datetime
from bson import ObjectId
from database.database import alarms_collection

class AlarmManagerInput(BaseModel):
    user_id: str = Field(..., description="The unique identifier for the user.")
    action: Literal["add", "remove", "update", "fetch"] = Field(..., description="The action to perform: 'add', 'remove', 'update', or 'fetch'.")
    query: Optional[dict] = Field(None, description="The query object containing the necessary fields for the specified action.")

class AlarmManagerTool(BaseTool):
    name: str = "AlarmManager"
    description: str = (
        "A tool to manage alarms by adding, removing, updating, or fetching them from the database. "
        "The input fields must follow specific requirements:\n\n"
        "1. `alarm_time`: Required for 'add' and 'update'. Must be in ISO 8601 format (e.g., '2024-12-26T22:00:00+05:30') "
        "and must always use the '+05:30' timezone.\n"
        "2. `repeat_pattern`: Specifies recurrence. Allowed values: 'none', 'daily', 'weekly', 'monthly'.\n"
        "3. `priority`: Specifies importance. Allowed values: 'normal', 'medium', 'high'.\n"
        "4. `tags`: Optional. A list of tags or keywords for categorization.\n"
        "5. `description`: Optional. A note explaining the alarm's purpose.\n"
        "6. `is_active`: Optional. Indicates whether the alarm is active (default: True).\n\n"
        "Actions:\n"
        "1. 'add': Creates a new alarm with required fields.\n"
        "2. 'remove': Deletes alarms matching the criteria.\n"
        "3. 'update': Modifies existing alarms. Requires both a 'filter' and 'update' object in the query.\n"
        "4. 'fetch': Retrieves alarms based on specified criteria."
    )
    args_schema: Type[BaseModel] = AlarmManagerInput

    def _run(self, user_id: str, action: str, query: Optional[dict] = None):
        if action == "add":
            if query is None:
                return {"status": "error", "message": "Query must be provided for adding an alarm."}
            
            query["user_id"] = ObjectId(user_id)  # Add user ID to the query
            query["is_active"] = True
            query["created_at"] = datetime.now()
            result = alarms_collection.insert_one(query)
            query["user_id"] = str(user_id)
            return {"status": "success", "message": "Alarm added successfully.", "alarm_id": str(result.inserted_id)}

        elif action == "remove":
            query["user_id"] = ObjectId(user_id)  # Ensure user-specific deletion
            if "_id" in query:
                query["_id"] = ObjectId(query["_id"])
            result = alarms_collection.delete_many(query)
            query["user_id"] = str(user_id)
            query["_id"] = str(query["_id"])
            return {"status": "success", "message": f"{result.deleted_count} alarms removed successfully."}

        elif action == "update":
            try:
                if "filter" not in query or "update" not in query:
                    return {"status": "error", "message": "'filter' and 'update' fields are required for update action."}

                if not isinstance(query["filter"], dict) or not isinstance(query["update"], dict):
                    return {"status": "error", "message": "Both 'filter' and 'update' must be valid dictionaries."}

                # Convert user_id and _id to ObjectId where necessary
                query["filter"]["user_id"] = ObjectId(user_id)
                if "_id" in query["filter"]:
                    query["filter"]["_id"] = ObjectId(query["filter"]["_id"])

                # Perform the update
                result = alarms_collection.update_many(query["filter"], {"$set": query["update"]})

                query["filter"]["user_id"] = str(query["filter"]["user_id"])
                if "_id" in query["filter"]:
                    query["filter"]["_id"] = str(query["filter"]["_id"])

                # Return only the success message and number of documents updated
                return {
                    "status": "success",
                    "message": f"{result.raw_result} alarms updated successfully."
                }
            except Exception as e:
                print("Error:", str(e))
                return {"status": "error", "message": str(e)}



        elif action == "fetch":
            if query is None:
                query = {}  # Default to an empty query if none is provided
            query["user_id"] = ObjectId(user_id)  # Ensure user-specific fetching
            if "_id" in query:
                query["_id"] = ObjectId(query["_id"])
            
            alarms = list(alarms_collection.find(query))
            query["user_id"] = str(user_id) 
            for alarm in alarms:
                if "_id" in alarm:
                    alarm["_id"] = str(alarm["_id"])
                if "user_id" in alarm:
                    alarm["user_id"] = str(alarm["user_id"])
            return {"status": "success", "data": alarms}

        else:
            return {"status": "error", "message": "Invalid action specified."}

    async def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async functionality is not implemented yet.")