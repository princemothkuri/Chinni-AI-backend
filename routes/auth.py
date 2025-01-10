from fastapi import APIRouter, HTTPException
from controllers.loginController import verify_login
from controllers.registerController import save_user_to_database
from controllers.passwordResetController import verify_reset_request, update_password
from models import RegisterUser, LoginUser, PasswordResetRequest, PasswordResetConfirm

router = APIRouter()

@router.post("/register")
async def register(user: RegisterUser):
    res = save_user_to_database(user)
    return res

@router.post("/login")
async def login(credentials: LoginUser):
    res = verify_login(credentials)
    
    if "error" in res:
        raise HTTPException(
            status_code=res["status"],
            detail=res["error"]
        )
    
    return res

@router.post("/reset-password/verify")
async def reset_password_verify(reset_request: PasswordResetRequest):
    res = await verify_reset_request(reset_request)
    
    if "error" in res:
        raise HTTPException(
            status_code=res["status"],
            detail=res["error"]
        )
    
    return res

@router.post("/reset-password/confirm")
async def reset_password_confirm(reset_confirm: PasswordResetConfirm):
    res = await update_password(reset_confirm)
    
    if "error" in res:
        raise HTTPException(
            status_code=res["status"],
            detail=res["error"]
        )
    
    return res
