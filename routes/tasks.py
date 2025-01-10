from fastapi import APIRouter, Request, HTTPException
from controllers.taskController import TaskController
from utils.jwt_handler import get_current_user
from pydantic import BaseModel

router = APIRouter()
task_controller = TaskController()

class StatusUpdate(BaseModel):
    new_status: str

class SubtaskStatusUpdate(BaseModel):
    new_status: str

@router.post("/tasks")
async def add_task(request: Request, task_data: dict):
    user_id = get_current_user(request)
    return await task_controller.add_task(user_id, task_data)

@router.get("/tasks")
async def fetch_tasks(request: Request, filters: dict = None):
    user_id = get_current_user(request)
    return await task_controller.fetch_tasks(user_id, filters)

@router.get("/tasks/{task_id}")
async def fetch_task(task_id: str, request: Request):
    user_id = get_current_user(request)
    return await task_controller.fetch_task(user_id, task_id)

@router.put("/tasks/{task_id}")
async def update_task(task_id: str, request: Request, update_data: dict):
    user_id = get_current_user(request)
    return await task_controller.update_task(user_id, task_id, update_data)

@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str, request: Request):
    user_id = get_current_user(request)
    return await task_controller.delete_task(user_id, task_id)

# Subtask routes
@router.post("/tasks/{task_id}/subtasks")
async def add_subtask(task_id: str, request: Request, subtask_data: dict):
    user_id = get_current_user(request)
    return await task_controller.add_subtask(user_id, task_id, subtask_data)

@router.get("/tasks/{task_id}/subtasks")
async def get_subtasks(task_id: str, request: Request):
    user_id = get_current_user(request)
    return await task_controller.get_subtasks(user_id, task_id)

@router.put("/tasks/{task_id}/subtasks/{subtask_id}")
async def update_subtask(
    task_id: str,
    subtask_id: str,
    request: Request,
    update_data: dict
):
    user_id = get_current_user(request)
    return await task_controller.update_subtask(user_id, task_id, subtask_id, update_data)

@router.delete("/tasks/{task_id}/subtasks/{subtask_id}")
async def delete_subtask(task_id: str, subtask_id: str, request: Request):
    user_id = get_current_user(request)
    return await task_controller.delete_subtask(user_id, task_id, subtask_id)

# New route to change the status of a parent task
@router.put("/tasks/{task_id}/status")
async def change_task_status(task_id: str, request:Request, status_update: StatusUpdate):
    user_id = get_current_user(request)
    new_status = status_update.new_status
    valid_statuses = ["pending", "completed"]
    
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status. Only 'pending' or 'completed' are allowed.")
    
    return await task_controller.change_task_status(user_id, task_id, new_status)

# New route to change the status of a specific subtask
@router.put("/tasks/{task_id}/subtasks/{subtask_id}/status")
async def change_subtask_status(task_id: str, subtask_id: str, request: Request, status_update: SubtaskStatusUpdate):
    user_id = get_current_user(request)
    new_status = status_update.new_status
    valid_statuses = ["pending", "completed"]
    
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status. Only 'pending' or 'completed' are allowed.")
    
    return await task_controller.change_subtask_status(user_id, task_id, subtask_id, new_status)


