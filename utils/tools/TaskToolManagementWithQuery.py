from datetime import datetime, UTC
from typing import Optional, Literal, Type
from pydantic import BaseModel, Field
from bson import ObjectId
from langchain.tools import BaseTool
from database.database import tasks_collection

class TaskManagerInput(BaseModel):
    user_id: str = Field(..., description="The unique identifier for the user (Don't dare to ask the user_id to the user.).")
    action: Literal["add", "remove", "update", "fetch"] = Field(..., description="The action to perform: 'add', 'remove', 'update', or 'fetch'.")
    query: Optional[dict] = Field(None, description="The query object containing the necessary fields for the specified action.")


class TaskManagerTool(BaseTool):
    name: str = "TaskManager"

    description: str = (
        "A tool to manage tasks and subtasks by adding, removing, updating, or fetching them from the database. "
        "Key fields include `title` (required for 'add'), `description`, `due_date` (ISO 8601), `priority` ('low', 'normal', 'high'), "
        "`status` ('pending', 'completed'), `tags`, and `subtasks` (array with similar fields).\n\n"
        "Actions:\n"
        "1. 'add': Creates a task or subtask with required fields and auto-generated IDs.\n"
        "2. 'remove': Deletes tasks/subtasks matching filters. For subtasks, requires 'update' in the query.\n"
        "3. 'update': Modifies tasks/subtasks using 'filter' and 'update' in the query.\n"
        "4. 'fetch': Retrieves tasks/subtasks based on query criteria."
    )



    args_schema: Type[BaseModel] = TaskManagerInput

    def _run(self, user_id, action, query):

        if action == "add":
            return self.add_task(user_id, query)
        elif action == "update":
            return self.update_task(user_id, query)
        elif action == "remove":
            return self.remove_task(user_id, query)
        elif action == "fetch":
            return self.fetch_tasks(user_id, query)
        else:
            raise ValueError("Invalid action")

    def _arun(self, user_id, action, query):
        raise NotImplementedError("Async execution is not supported.")

    def add_task(self, user_id, query):
        try:
            # Convert user_id to ObjectId for DB operation
            query["user_id"] = ObjectId(user_id)
            query["created_at"] = datetime.now(UTC)
            query["last_updated"] = datetime.now(UTC)
            
            # Handle subtasks ObjectIds
            subtasks = query.get("subtasks", [])
            for subtask in subtasks:
                if "_id" not in subtask:
                    subtask["_id"] = ObjectId()

                    
            # Insert into DB
            result = tasks_collection.insert_one(query)
            
            # Convert ObjectIds back to strings
            query["user_id"] = str(query["user_id"])
            query["_id"] = str(query["_id"])
            for subtask in subtasks:
                subtask["_id"] = str(subtask["_id"])
                
            return {"status": "success", "inserted_id": str(result.inserted_id)}
        except Exception as e:
            # print("Error while adding: ", str(e))
            return {"status": "error", "Error while adding": str(e)}

    def update_task(self, user_id, query):
        try:
            filter_query = query.get("filter", {})
            update_query = query.get("update", {})

            # Convert user_id and filter _id to ObjectId
            filter_query["user_id"] = ObjectId(user_id)
            filter_query = self._convert_ids_to_objectid(filter_query)

            # Process $push subtasks
            if "$push" in update_query and "subtasks" in update_query["$push"]:
                update_query["$push"]["subtasks"] = self._process_subtasks(update_query["$push"]["subtasks"])

            # Process $pull subtasks
            if "$pull" in update_query and "subtasks" in update_query["$pull"]:
                subtasks = update_query["$pull"]["subtasks"]
                if isinstance(subtasks, dict) and "_id" in subtasks:
                    if isinstance(subtasks["_id"], str):
                        update_query["$pull"]["subtasks"]["_id"] = ObjectId(subtasks["_id"])

            # Skip updating _id fields in $set
            if "$set" in update_query:
                update_query["$set"] = {k: v for k, v in update_query["$set"].items() if not k.endswith("._id")}

            # Add or update last_updated field
            update_query.setdefault("$set", {})["last_updated"] = datetime.now(UTC)

            # Apply the update query to the collection
            result = tasks_collection.update_one(filter_query, update_query)

            # Convert ObjectIds back to strings for response
            filter_query = self._convert_object_ids_to_str(filter_query)
            update_query = self._convert_update_query_object_ids_to_str(update_query)

            if result.modified_count > 0:
                return {"status": "success", "message": "Task updated successfully"}
            else:
                return {"status": "no_update", "message": "No documents were updated"}
        except Exception as e:
            # print("Error while updating: ", str(e))
            return {"status": "error", "message": str(e), "query": query}


    # Helper Methods
    def _convert_ids_to_objectid(self, data):
        """Recursively convert string IDs in filters to ObjectId."""
        if isinstance(data, dict):
            for key, value in data.items():
                if key.endswith("_id") and isinstance(value, str):
                    data[key] = ObjectId(value)
                elif isinstance(value, dict) or isinstance(value, list):
                    data[key] = self._convert_ids_to_objectid(value)
        elif isinstance(data, list):
            return [self._convert_ids_to_objectid(item) for item in data]
        return data

    def _process_subtasks(self, subtasks):
        """Ensure subtasks have ObjectIds."""
        if isinstance(subtasks, dict) and "$each" in subtasks:
            for subtask in subtasks["$each"]:
                subtask["_id"] = ObjectId(subtask.get("_id", str(ObjectId())))
        elif isinstance(subtasks, dict):
            subtasks["_id"] = ObjectId(subtasks.get("_id", str(ObjectId())))
        return subtasks


    def _convert_object_ids_to_str(self, data):
        """Recursively convert ObjectIds to strings in a dictionary."""
        if isinstance(data, dict):
            return {key: self._convert_object_ids_to_str(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._convert_object_ids_to_str(item) for item in data]
        elif isinstance(data, ObjectId):
            return str(data)
        elif isinstance(data, datetime):
            return data.isoformat() 
        return data

    def _convert_update_query_object_ids_to_str(self, update_query):
        """Special handling for update queries to convert ObjectIds."""
        if "$push" in update_query and "subtasks" in update_query["$push"]:
            subtasks = update_query["$push"]["subtasks"]
            if isinstance(subtasks, dict) and "$each" in subtasks:
                update_query["$push"]["subtasks"]["$each"] = [
                    self._convert_object_ids_to_str(subtask) for subtask in subtasks["$each"]
                ]
            elif isinstance(subtasks, dict):
                update_query["$push"]["subtasks"] = self._convert_object_ids_to_str(subtasks)

        if "$set" in update_query:
            update_query["$set"] = self._convert_object_ids_to_str(update_query["$set"])

        return update_query

    def remove_task(self, user_id, query):
        try:
            filter_query = query.get("filter", {})
            update_query = query.get("update", {})

            filter_query["user_id"] = ObjectId(user_id)
            query["user_id"] = ObjectId(user_id)

            # Convert _id to ObjectId if necessary
            if "_id" in filter_query:
                filter_query["_id"] = ObjectId(filter_query["_id"])
            if "subtasks._id" in update_query.get("$pull", {}).get("subtasks", {}):
                update_query["$pull"]["subtasks"]["_id"] = ObjectId(update_query["$pull"]["subtasks"]["_id"])

            if update_query:
                result = tasks_collection.update_one(filter_query, update_query)
            else:
                result = tasks_collection.delete_one(filter_query)

            # Convert ObjectIds back to strings
            if "_id" in filter_query:
                filter_query["_id"] = str(filter_query["_id"])
            query["user_id"] = str(user_id)
            filter_query["user_id"] = str(filter_query["user_id"])
            
            if update_query and "$pull" in update_query and "subtasks" in update_query["$pull"]:
                if "_id" in update_query["$pull"]["subtasks"]:
                    update_query["$pull"]["subtasks"]["_id"] = str(update_query["$pull"]["subtasks"]["_id"])

            return {"status": "success", "message": "Task removed successfully"}
        except Exception as e:
            # print("Error while removing: ", str(e))
            return {"status": "error", "Error while removing": str(e)}

    def fetch_tasks(self, user_id, query):
        try:
            filter_query = {k: (ObjectId(v) if k == "_id" else v) for k, v in query.items()}
            filter_query["user_id"] = ObjectId(user_id)
            
            # Get tasks from DB
            tasks = list(tasks_collection.find(filter_query))
            
            # Convert ObjectId to string for JSON serialization
            filter_query = {k: (str(v) if k == "_id" else v) for k, v in query.items()}
            filter_query["user_id"] = str(user_id)
            if "_id" in filter_query:
                filter_query["_id"] = str(filter_query["_id"])

            tasks = self._convert_object_ids_to_str(tasks)
            
            return {"status": "success", "tasks": tasks}
        except Exception as e:
            # print("Error while fetching: ", str(e))
            return {"status": "error", "Error while fetching": str(e)}
