from fastapi import APIRouter, Request
from controllers.profileController import update_user_profile
from controllers.settingsController import save_api_key_to_database, get_api_key_from_database
from controllers.deleteAccountController import delete_user_account
from pydantic import BaseModel

from utils.jwt_handler import get_current_user

router = APIRouter()

class APIKey(BaseModel):
    OpenAI_Api_Key: str

class UserProfile(BaseModel):
    firstName: str
    lastName: str
    username: str
    email: str
    # Add other fields as necessary

@router.post("/set-api-key")
async def register(request: Request, apiKey: APIKey):
    user_id = get_current_user(request)
    res = save_api_key_to_database(user_id, apiKey.OpenAI_Api_Key)
    return res

@router.get("/get-api-key")
async def get_api_key(request: Request):
    user_id = get_current_user(request)
    res = get_api_key_from_database(user_id)
    return res

@router.put("/update-profile")
async def update_profile(request: Request, profile: UserProfile):
    user_id = get_current_user(request)
    res = update_user_profile(user_id, profile.model_dump())
    return res

@router.delete("/delete-account")
async def delete_account(request: Request):
    user_id = get_current_user(request)
    res = delete_user_account(user_id)
    return res
