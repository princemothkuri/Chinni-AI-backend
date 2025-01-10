from fastapi import APIRouter, Depends, HTTPException
from database.database import users_collection
from utils.jwt_handler import get_current_user

router = APIRouter()

@router.get("/profile")
async def get_profile(current_user: str = Depends(get_current_user)):
    user = users_collection.find_one({"_id": current_user}, {"_id": 0, "full_name": 1, "username": 1, "email": 1})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
