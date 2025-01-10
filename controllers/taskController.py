from fastapi import HTTPException
from bson import ObjectId
from datetime import datetime, UTC
from database.database import tasks_collection
from utils.DateTimeConvertions import convert_from_iso, convert_to_iso

def parse_custom_date(date_str):
    try:
        # Parse the custom date format
        parsed_date = datetime.strptime(date_str, '%d %B, %I:%M %p %Y')
        return parsed_date.strftime('%d %B, %I:%M %p %Y')  # Updated format
    except ValueError as e:
        raise ValueError(f"Invalid date format: {date_str}. Error: {str(e)}")

class TaskController:
    @staticmethod
    async def add_task(user_id, task_data):
        try:
            due_datetime_iso = convert_to_iso(task_data.get("due_date")) if task_data.get("due_date") else None
            task_data = {
                "user_id": ObjectId(user_id),
                "title": task_data.get("title"),
                "description": task_data.get("description"),
                "due_date": due_datetime_iso,
                "status": task_data.get("status", "pending"),
                "priority": task_data.get("priority", "medium"),
                "tags": task_data.get("tags", []),
                "subtasks": task_data.get("subtasks", []),
                "created_at": datetime.now(UTC),
                "last_updated": datetime.now(UTC),
            }
            # Ensure each subtask has a unique ObjectId
            for subtask in task_data.get("subtasks", []):
                if "_id" not in subtask:
                    subtask["_id"] = ObjectId()  # Assign a new ObjectId if not present
                if "due_date" in subtask:
                    subtask["due_date"] = convert_to_iso(subtask.get("due_date")) if subtask.get("due_date") else None
            result = tasks_collection.insert_one(task_data)
            task_data["_id"] = str(result.inserted_id)

            task_data.pop("user_id", None)

            try:
                task_data["due_date"] = convert_from_iso(task_data["due_date"])
            except ValueError:
                task_data["due_date"] = parse_custom_date(task_data["due_date"])

            for subtask in task_data.get("subtasks", []):
                subtask["_id"] = str(subtask["_id"])
                if "due_date" in subtask and subtask["due_date"]:
                    try:
                        subtask["due_date"] = convert_from_iso(subtask["due_date"])
                    except ValueError:
                        subtask["due_date"] = parse_custom_date(subtask["due_date"])

            return {"task_data": task_data}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to add task: {str(e)}")

    @staticmethod
    async def fetch_tasks(user_id, filters=None):
        try:
            query = {"user_id": ObjectId(user_id)}
            if filters:
                if "title" in filters:
                    query["title"] = {"$regex": filters["title"], "$options": "i"}
                if "status" in filters:
                    query["status"] = filters["status"]
                if "priority" in filters:
                    query["priority"] = filters["priority"]
                if "tags" in filters:
                    query["tags"] = {"$in": filters["tags"]}
            tasks = list(tasks_collection.find(query))
            for task in tasks:
                if "due_date" in task and task["due_date"]:
                    try:
                        task["due_date"] = convert_from_iso(task["due_date"])
                    except ValueError:
                        task["due_date"] = parse_custom_date(task["due_date"])
                task["_id"] = str(task["_id"])
                task.pop("user_id", None)

                for subtask in task.get("subtasks", []):
                    subtask["_id"] = str(subtask["_id"])
                    if "due_date" in subtask and subtask["due_date"]:
                        try:
                            subtask["due_date"] = convert_from_iso(subtask["due_date"])
                        except ValueError:
                            subtask["due_date"] = parse_custom_date(subtask["due_date"])

            return tasks
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch tasks: {str(e)}")
    
    @staticmethod
    async def fetch_task(user_id, task_id):
        try:
            query = {"_id": ObjectId(task_id), "user_id": ObjectId(user_id)}
            task = tasks_collection.find_one(query)
            if not task:
                raise HTTPException(status_code=404, detail="Task not found.")
            task["_id"] = str(task["_id"])
            task["user_id"] = str(task["user_id"])
            # Convert due_date if present
            if "due_date" in task and task["due_date"]:
                task["due_date"] = convert_from_iso(task["due_date"])

            for subtask in task.get("subtasks", []):
                subtask["_id"] = str(subtask["_id"])
                if "due_date" in subtask and subtask["due_date"]:
                    try:
                        subtask["due_date"] = convert_from_iso(subtask["due_date"])
                    except ValueError:
                        subtask["due_date"] = parse_custom_date(subtask["due_date"])

            task.pop("user_id", None)

            return task
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch task: {str(e)}")

    @staticmethod
    async def update_task(user_id, task_id, update_data):
        try:
            query = {"_id": ObjectId(task_id), "user_id": ObjectId(user_id)}
            if "due_date" in update_data:
                update_data["due_date"] = convert_to_iso(update_data["due_date"])
            update_data["last_updated"] = datetime.now(UTC)
            update_data.pop("_id", None)
            update_data = {k: v for k, v in update_data.items() if v is not None}

            tasks_collection.update_one(query, {"$set": {"subtasks": []}})  # Remove all existing subtasks

            if "subtasks" in update_data:
                for subtask in update_data["subtasks"]:
                    if "_id" not in subtask or subtask["_id"] == "":
                        subtask["_id"] = ObjectId()
                    if "due_date" in subtask:
                        subtask["due_date"] = convert_to_iso(subtask.get("due_date")) if subtask.get("due_date") else None
                
                tasks_collection.update_one(query, {"$push": {"subtasks": {"$each": update_data["subtasks"]}}})

            result = tasks_collection.update_one(query, {"$set": update_data}) 
            if result.modified_count == 0:
                raise HTTPException(status_code=404, detail="Task not found or no changes made.")
            return {"message": "Task updated successfully."}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update task: {str(e)}")

    @staticmethod
    async def delete_task(user_id, task_id):
        try:
            query = {"_id": ObjectId(task_id), "user_id": ObjectId(user_id)}
            result = tasks_collection.delete_one(query)
            if result.deleted_count == 0:
                raise HTTPException(status_code=404, detail="Task not found.")
            return {"message": "Task deleted successfully."}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete task: {str(e)}")

    @staticmethod
    async def add_subtask(user_id, task_id, subtask_data):
        try:
            query = {"_id": ObjectId(task_id), "user_id": ObjectId(user_id)}
            subtask = {
                "_id": ObjectId(),  # Generate new ObjectId for subtask
                "title": subtask_data.get("title"),
                "description": subtask_data.get("description"),
                "status": subtask_data.get("status", "pending"),
                "created_at": datetime.now(UTC),
                "last_updated": datetime.now(UTC)
            }
            
            # Convert due_date to ISO format if present
            if "due_date" in subtask_data:
                subtask["due_date"] = convert_to_iso(subtask_data["due_date"])

            result = tasks_collection.update_one(
                query,
                {"$push": {"subtasks": subtask}}
            )
            
            if result.modified_count == 0:
                raise HTTPException(status_code=404, detail="Task not found")
            
            return {
                "message": "Subtask added successfully",
                "subtask_id": str(subtask["_id"])
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to add subtask: {str(e)}")

    @staticmethod
    async def update_subtask(user_id, task_id, subtask_id, update_data):
        try:
            # Prepare update data with timestamp
            update_data["last_updated"] = datetime.now(UTC)
            
            # Create the update query for the specific subtask
            result = tasks_collection.update_one(
                {
                    "_id": ObjectId(task_id),
                    "user_id": ObjectId(user_id),
                    "subtasks._id": ObjectId(subtask_id)
                },
                {
                    "$set": {
                        "subtasks.$.title": update_data.get("title"),
                        "subtasks.$.description": update_data.get("description"),
                        "subtasks.$.status": update_data.get("status"),
                        "subtasks.$.last_updated": update_data["last_updated"]
                    }
                }
            )

            if result.modified_count == 0:
                raise HTTPException(status_code=404, detail="Task or subtask not found")
            
            return {"message": "Subtask updated successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update subtask: {str(e)}")

    @staticmethod
    async def delete_subtask(user_id, task_id, subtask_id):
        try:
            result = tasks_collection.update_one(
                {
                    "_id": ObjectId(task_id),
                    "user_id": ObjectId(user_id)
                },
                {
                    "$pull": {
                        "subtasks": {"_id": ObjectId(subtask_id)}
                    }
                }
            )

            if result.modified_count == 0:
                raise HTTPException(status_code=404, detail="Task or subtask not found")
            
            return {"message": "Subtask deleted successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete subtask: {str(e)}")

    @staticmethod
    async def get_subtasks(user_id, task_id):
        try:
            task = tasks_collection.find_one(
                {
                    "_id": ObjectId(task_id),
                    "user_id": ObjectId(user_id)
                }
            )

            if not task:
                raise HTTPException(status_code=404, detail="Task not found")

            subtasks = task.get("subtasks", [])
            # Convert ObjectIds to strings for JSON serialization
            for subtask in subtasks:
                subtask["_id"] = str(subtask["_id"])

            return subtasks
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch subtasks: {str(e)}")

    @staticmethod
    async def change_task_status(user_id, task_id, new_status):
        try:
            query = {"_id": ObjectId(task_id), "user_id": ObjectId(user_id)}
            update_data = {"status": new_status, "last_updated": datetime.now(UTC)}
            
            # Update the parent task status
            result = tasks_collection.update_one(query, {"$set": update_data})
            if result.modified_count == 0:
                raise HTTPException(status_code=404, detail="Task not found or no changes made.")
            
            return {"message": "Task status updated successfully."}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to change task status: {str(e)}")

    @staticmethod
    async def change_subtask_status(user_id, task_id, subtask_id, new_status):
        try:
            query = {
                "_id": ObjectId(task_id),
                "user_id": ObjectId(user_id),
                "subtasks._id": ObjectId(subtask_id)
            }
            update_data = {
                "subtasks.$.status": new_status,
                "subtasks.$.last_updated": datetime.now(UTC)
            }
            
            # Update the specific subtask status
            result = tasks_collection.update_one(query, {"$set": update_data})
            if result.modified_count == 0:
                raise HTTPException(status_code=404, detail="Task or subtask not found.")
            
            return {"message": "Subtask status updated successfully."}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to change subtask status: {str(e)}")

    