from utils import groqLLM
from .system_prompts.demo_system_prompt import demo_system_prompt

def demoAgent(user_message: str):
        
    try:
        res = groqLLM.groqLLMApi(system_prompt=demo_system_prompt, user_message=user_message)
        
        return res
        
    except Exception as e:
        return "I apologize, but I'm having trouble processing your request. Please try again later."
