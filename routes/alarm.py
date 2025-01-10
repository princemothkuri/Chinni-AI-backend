from fastapi import APIRouter, Request
from controllers.alarmController import AlarmController
from utils.jwt_handler import get_current_user

router = APIRouter()
alarm_controller = AlarmController()

@router.get("/alarms")
async def get_alarms(request: Request):
    user_id = get_current_user(request)
    return await alarm_controller.get_user_alarms(user_id)

@router.post("/alarms")
async def add_alarm(request: Request, alarm_data: dict):
    user_id = get_current_user(request)
    return await alarm_controller.create_alarm(user_id, alarm_data)

@router.put("/alarms/{alarm_id}")
async def update_alarm(alarm_id: str, request: Request, update_data: dict):
    user_id = get_current_user(request)
    return await alarm_controller.update_alarm(alarm_id, user_id, update_data)

@router.patch("/alarms/{alarm_id}/toggle")
async def toggle_alarm(alarm_id: str, request: Request):
    user_id = get_current_user(request)
    return await alarm_controller.toggle_alarm(alarm_id, user_id)

@router.delete("/alarms/{alarm_id}")
async def delete_alarm(alarm_id: str, request: Request):
    user_id = get_current_user(request)
    return await alarm_controller.delete_alarm(alarm_id, user_id)
