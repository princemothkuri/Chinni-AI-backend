import json
from utils.groqLLM import groqLLMApi
from utils.system_prompts.tags_system_prompt import tagging_system_prompt

def assign_tags(description: str, title: str = "") -> list:
    while True:
        # Call the LLM API to get tags
        response = groqLLMApi(
            system_prompt=tagging_system_prompt,
            user_message=f"Title: '{title}', Description: '{description}'"
        )
        
        try:
            # Attempt to parse the response as JSON
            tags = json.loads(response)
            
            # Check if the parsed response is a list
            if isinstance(tags, list):
                return tags
        except json.JSONDecodeError:
            # If parsing fails, continue the loop to make another API call
            continue
    
    
