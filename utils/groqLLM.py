from groq import Groq
from dotenv import load_dotenv
import os

# Load .env variables into the environment
load_dotenv()

GROQ_API_KEY = os.getenv('GROQ_API_KEY')


def groqLLMApi(system_prompt:str, user_message:str):
    client = Groq(api_key=GROQ_API_KEY)
    
    # Format messages for the chat
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=messages,
            temperature=0.7,
            max_tokens=1024,
            top_p=1
        )
        
        return completion.choices[0].message.content
        
    except Exception as e:
        return "I apologize, but I'm having trouble processing your request. Please try again later."
