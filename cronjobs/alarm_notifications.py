from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import pytz
from database.database import alarms_collection, users_collection
import asyncio
import json
import logging
from routes.health import update_last_check
from .websocket_store import get_websocket

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("alarm_cron")

async def check_and_notify_alarms():
    """Check for due alarms and notify users"""
    try:
        # Update health check timestamp
        update_last_check()
        
        # Get current time in Asia/Kolkata timezone
        kolkata_tz = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(kolkata_tz)
        formatted_time = current_time.strftime('%Y-%m-%dT%H:%M:%S%z')
        # Insert colon in timezone offset
        formatted_time = formatted_time[:-2] + ':' + formatted_time[-2:]
        logger.debug(f"Checking alarms at: {current_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
        
        # Find all active alarms that are due
        due_alarms = alarms_collection.find({
            "alarm_time": {"$lte": formatted_time},
            "is_active": True
        })

        for alarm in due_alarms:
            user_id = alarm["user_id"]
            
            # Get user's socket_id
            user = users_collection.find_one({"_id": user_id})
            if not user or "socket_id" not in user:
                continue

            socket_id = user["socket_id"]
            websocket = get_websocket(socket_id)
            if not websocket:
                continue
            
            # Prepare notification message
            notification = {
                "type": "alarm_notification",
                "data": {
                    "alarm_id": str(alarm["_id"]),
                    "description": alarm.get("description", "Alarm!"),
                    "priority": alarm.get("priority", "normal"),
                    "tags": alarm.get("tags", []),
                    "time": alarm["alarm_time"]
                }
            }

            # Calculate next alarm time if it's a recurring alarm
            next_alarm_time = None
            current_alarm_time = datetime.fromisoformat(alarm["alarm_time"])

            if alarm.get("repeat_pattern") == "daily":
                next_alarm_time = current_alarm_time + timedelta(days=1)
            elif alarm.get("repeat_pattern") == "weekly":
                next_alarm_time = current_alarm_time + timedelta(days=7)
            elif alarm.get("repeat_pattern") == "monthly":
                next_alarm_time = current_alarm_time + relativedelta(months=1)

            if next_alarm_time:
                # Format as ISO 8601 with timezone information
                next_alarm_time = next_alarm_time.isoformat()

                # Insert colon in timezone offset if needed (fix formatting if required)
                if '+' in next_alarm_time or '-' in next_alarm_time:
                    if ':' not in next_alarm_time[-6:]:
                        next_alarm_time = (
                            next_alarm_time[:-2] + ':' + next_alarm_time[-2:]
                        )
                
                # Update the notification with the formatted string
                notification["data"]["next_alarm_time"] = next_alarm_time

            try:
                # Send notification through WebSocket
                await websocket.send_text(json.dumps(notification))

                # Update alarm based on repeat pattern
                if alarm.get("repeat_pattern") == "daily":
                    
                    alarms_collection.update_one(
                        {"_id": alarm["_id"]},
                        {"$set": {"alarm_time": next_alarm_time}}
                    )
                elif alarm.get("repeat_pattern") == "weekly":
                    
                    alarms_collection.update_one(
                        {"_id": alarm["_id"]},
                        {"$set": {"alarm_time": next_alarm_time}}
                    )
                elif alarm.get("repeat_pattern") == "monthly":
                    
                    alarms_collection.update_one(
                        {"_id": alarm["_id"]},
                        {"$set": {"alarm_time": next_alarm_time}}
                    )
                else:
                    # For non-repeating alarms, mark as inactive
                    alarms_collection.update_one(
                        {"_id": alarm["_id"]},
                        {"$set": {"is_active": False}}
                    )

            except Exception as e:
                logger.error(f"Error sending notification: {str(e)}")
                continue

    except Exception as e:
        logger.error(f"Error in alarm notification cron: {str(e)}")

async def start_alarm_cron():
    """Start the alarm notification cron job"""
    logger.info("🚀 Starting alarm notification cron job")
    tick_count = 0
    
    while True:
        # tick_count += 1
        # if tick_count % 60 == 0:  # Log every minute
        #     logger.info(f"✅ Alarm cron still running... (tick: {tick_count})")
        await check_and_notify_alarms()
        await asyncio.sleep(1)  # Check every second