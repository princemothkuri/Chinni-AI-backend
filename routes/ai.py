from fastapi import APIRouter, Depends
from models import UserMessage
from utils.jwt_handler import get_current_user
from utils.agent import chinniAiAgent
from utils.demoAgent import demoAgent

router = APIRouter()

@router.post("/chat")
def post_user_message(
    chat_request: UserMessage, 
    current_user = Depends(get_current_user)
):
    response = chinniAiAgent(
        user_id=current_user, 
        user_message=chat_request.message
    )
    return { "response": response } 

@router.post("/demo-chat")
def post_demo_message(chat_request: UserMessage):
    response = demoAgent(user_message=chat_request.message)
    return {"response": response} 