from fastapi import HTTPException
from bson import ObjectId
from database.database import alarms_collection
from datetime import datetime
from utils.tag_assigner import assign_tags

class AlarmController:
    @staticmethod
    async def get_user_alarms(user_id):
        alarms = list(alarms_collection.find(
            {"user_id": ObjectId(user_id)}
        ).sort("created_at", -1))
        for alarm in alarms:
            alarm["_id"] = str(alarm["_id"])
            del alarm["user_id"]
        return alarms

    @staticmethod
    async def create_alarm(user_id, alarm_data):
        try:
            # Wait for tags to be generated
            max_retries = 3
            retry_count = 0
            tags = None
            
            while retry_count < max_retries:
                try:
                    tags = assign_tags(
                        description=alarm_data.get("description", ""),
                        title=alarm_data.get("title", "")
                    )
                    if tags:  # If we got valid tags, break the loop
                        break
                except Exception as e:
                    retry_count += 1
                    if retry_count == max_retries:
                        raise HTTPException(
                            status_code=500,
                            detail="Failed to generate tags. Please try again later."
                        )
            alarm_data["user_id"] = ObjectId(user_id)
            alarm_data["is_active"] = True
            alarm_data["alarm_time"] = alarm_data["alarm_time"] + ":00+05:30"
            alarm_data["created_at"] = datetime.now()
            alarm_data["tags"] = tags 
            res = alarms_collection.insert_one(alarm_data)
            
            # Remove the tags field from the returned alarm data
            del alarm_data["tags"]
            alarm_data["user_id"] = str(user_id)
            
            # Include the _id of the inserted document
            alarm_data["_id"] = str(res.inserted_id)
            
            return {
                "newAlarm": alarm_data
            }
        
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail="Failed to create alarm. Please try again later."
            )

    @staticmethod
    async def update_alarm(alarm_id, user_id, update_data):
        update_data['alarm_time'] = update_data['alarm_time'] + ":00+05:30"
        update_data['is_active'] = True
        result = alarms_collection.update_one(
            {"_id": ObjectId(alarm_id), "user_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Alarm not found")
        return {"message": "Alarm updated successfully"}

    @staticmethod
    async def toggle_alarm(alarm_id, user_id):
        alarm = alarms_collection.find_one({"_id": ObjectId(alarm_id), "user_id": ObjectId(user_id)})
        if not alarm:
            raise HTTPException(status_code=404, detail="Alarm not found")
        new_status = not alarm.get("is_active", False)
        alarms_collection.update_one(
            {"_id": ObjectId(alarm_id), "user_id": ObjectId(user_id)},
            {"$set": {"is_active": new_status}}
        )
        return {"message": f"Alarm {'on' if new_status else 'off'}"}

    @staticmethod
    async def delete_alarm(alarm_id, user_id):
        result = alarms_collection.delete_one({"_id": ObjectId(alarm_id), "user_id": ObjectId(user_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Alarm not found")
        return {"message": "Alarm deleted successfully"}
