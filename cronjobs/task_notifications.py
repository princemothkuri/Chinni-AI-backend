from datetime import datetime, timedelta
import pytz
from database.database import tasks_collection, users_collection
import asyncio
import json
import logging
from routes.health import update_last_check
from .websocket_store import get_websocket

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("task_cron")

async def check_and_notify_tasks():
    """Check for upcoming tasks and notify users"""
    try:
        # Update health check timestamp
        update_last_check()
        
        # Get current time in Asia/Kolkata timezone
        kolkata_tz = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(kolkata_tz)
        formatted_current_time = current_time.strftime('%Y-%m-%dT%H:%M:%S%z')
        formatted_current_time = formatted_current_time[:-2] + ':' + formatted_current_time[-2:]
        
        # Check for tasks due in the next 24 hours
        next_24_hours = current_time + timedelta(hours=24)
        formatted_next_24_hours = next_24_hours.strftime('%Y-%m-%dT%H:%M:%S%z')
        formatted_next_24_hours = formatted_next_24_hours[:-2] + ':' + formatted_next_24_hours[-2:]

        logger.debug(f"Checking tasks at: {current_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")

        # Find all pending tasks that are due within 24 hours
        upcoming_tasks = tasks_collection.find({
            "$or": [
                {
                    "due_date": {
                        "$gte": current_time.isoformat(),
                        "$lte": next_24_hours.isoformat()
                    },
                    "status": "pending"
                },
                # Has pending subtasks with due dates in range
                {
                    "subtasks": {
                        "$elemMatch": {
                            "due_date": {
                                "$gte": current_time.isoformat(),
                                "$lte": next_24_hours.isoformat()
                            },
                            "status": "pending"
                        }
                    }
                }
            ]   
        })

        for task in upcoming_tasks:
            user_id = task["user_id"]
            
            # Get user's socket_id
            user = users_collection.find_one({"_id": user_id})
            if not user or "socket_id" not in user:
                continue

            socket_id = user["socket_id"]
            websocket = get_websocket(socket_id)
            if not websocket:
                continue

            # Check subtasks first
            has_due_subtasks = False
            for subtask in task.get("subtasks", []):
                if subtask.get("status") == "pending" and subtask.get("due_date"):
                    try:
                        subtask_due_date = datetime.fromisoformat(subtask["due_date"])
                        if current_time <= subtask_due_date <= next_24_hours:
                            has_due_subtasks = True
                            time_remaining = subtask_due_date - current_time
                            hours_remaining = time_remaining.total_seconds() / 3600

                            # Prepare notification with both parent and subtask info
                            notification = {
                                "type": "task_notification",
                                "data": {
                                    "task_id": str(task["_id"]),
                                    "title": task["title"],
                                    "description": task.get("description", ""),
                                    "due_date": task["due_date"],
                                    "priority": task.get("priority", "medium"),
                                    "tags": task.get("tags", []),
                                    "subtask": {
                                        "subtask_id": str(subtask.get("_id", "")),
                                        "title": subtask["title"],
                                        "description": subtask.get("description", ""),
                                        "due_date": subtask["due_date"],
                                        "priority": subtask.get("priority", task.get("priority", "medium")),
                                        "hours_remaining": round(hours_remaining, 1)
                                    }
                                }
                            }

                            try:
                                await websocket.send_text(json.dumps(notification))
                                logger.debug(f"Sent notification for task {task['title']} with subtask {subtask['title']}")
                            except Exception as e:
                                logger.error(f"Error sending notification: {str(e)}")
                                continue

                    except (ValueError, KeyError) as e:
                        logger.error(f"Error processing subtask: {str(e)}")
                        continue

            # If no due subtasks, check main task
            if not has_due_subtasks and task.get("status") == "pending" and task.get("due_date"):
                due_date = datetime.fromisoformat(task["due_date"])
                if current_time <= due_date <= next_24_hours:
                    time_remaining = due_date - current_time
                    hours_remaining = time_remaining.total_seconds() / 3600

                    # Prepare main task notification
                    notification = {
                        "type": "task_notification",
                        "data": {
                            "task_id": str(task["_id"]),
                            "title": task["title"],
                            "description": task.get("description", ""),
                            "due_date": task["due_date"],
                            "priority": task.get("priority", "medium"),
                            "tags": task.get("tags", []),
                            "hours_remaining": round(hours_remaining, 1)
                        }
                    }

                    try:
                        await websocket.send_text(json.dumps(notification))
                        logger.debug(f"Sent notification for task {task['title']}")
                    except Exception as e:
                        logger.error(f"Error sending notification: {str(e)}")
                        continue

    except Exception as e:
        logger.error(f"Error in task notification cron: {str(e)}")

async def start_task_cron():
    """Start the task notification cron job"""
    logger.info("🚀 Starting task notification cron job")
    tick_count = 0
    
    while True:
        # tick_count += 1
        # if tick_count % 300 == 0:  # Log every 5 minutes
        #     logger.info(f"✅ Task cron still running... (tick: {tick_count})")
        await check_and_notify_tasks()
        await asyncio.sleep(300)  # Check every 5 minutes, 300 