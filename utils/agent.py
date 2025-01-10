from pydantic import BaseModel
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from typing import List, Dict
import datetime
from controllers.settingsController import get_api_key_from_database
from bson import ObjectId
from utils.system_prompts.system_prompt import system_prompt
from database.database import messages_collection
from utils.tools.AlarmToolManagementWithQuery import AlarmManagerTool
from utils.tools.TaskToolManagementWithQuery import TaskManagerTool
from utils.tools.CurrentDateTime import CurrentDateTimeFetcher
from dotenv import load_dotenv
from utils.tools.GoogleSearchTool import GoogleSearchTool

# Load .env variables into the environment
load_dotenv()

# Define the Message class
class Message(BaseModel):
    sender: str
    message: str
    timestamp: str

class PersistentMemorySaver(MemorySaver):
    
    def store_messages(self, user_id: ObjectId, message_entries: list) -> None:
        """
        Stores multiple messages in the chat history for the specified user.
        """
        try:
            # Validate that each entry has the required fields
            for entry in message_entries:
                if "sender" not in entry or "message" not in entry or "timestamp" not in entry:
                    raise ValueError("Each message entry must include 'sender', 'message', and 'timestamp'")
                if entry["sender"] not in ["User", "Bot"]:
                    raise ValueError("Sender must be either 'User' or 'Bot'")

            # Upsert the document with the new messages
            messages_collection.update_one(
                {"user_id": user_id},
                {"$push": {"messages": {"$each": message_entries}}},
                upsert=True
            )
        except Exception as e:
            print(f"Error storing messages: {str(e)}")
            raise

    def retrieve_history(self, user_id: ObjectId) -> List[Dict]:
        try:
            # Get the document for this user_id and extract just the messages array
            result = messages_collection.find_one({"user_id": user_id})
            return result.get('messages', []) if result else []
        except Exception as e:
            print(f"Error retrieving history: {str(e)}")
            return []

memory = PersistentMemorySaver()
tools = [
    GoogleSearchTool(),
    CurrentDateTimeFetcher(),
    AlarmManagerTool(),
    TaskManagerTool()
]

def convert_objectid_to_str(data):
    if isinstance(data, dict):
        return {key: convert_objectid_to_str(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_objectid_to_str(item) for item in data]
    elif isinstance(data, ObjectId):
        return str(data)
    return data


def chinniAiAgent(user_message: str, user_id: ObjectId):
    try:
        # Convert user_id to string for JSON serialization
        user_id_str = str(user_id)

        # Retrieve chat history
        memory.retrieve_history(user_id=user_id)

        api_key = get_api_key_from_database(user_id=user_id)

        if api_key['api_key'] == "":
            return "It looks like you haven't set your OpenAI API key yet.\nPlease follow these steps to get started:\n1. **Get your API key**\nVisit the [OpenAI website](https://platform.openai.com/account/api-keys) to generate your API key.\n\n2. **Set the API key**\nGo to the [settings page](https://chinni-ai.vercel.app/settings) of ChinniAI Assistant and enter your API key.\n\nOnce you've set your API key, you're ready to use ChinniAI Assistant!"

        # Create agent executor
        agent_executor = create_react_agent(
            model=ChatOpenAI(model="gpt-4o-mini", api_key=api_key['api_key']),
            tools=tools, 
            checkpointer=memory,
            state_modifier=system_prompt
        )

        config = {
            "configurable": {
                "thread_id": user_id_str
            }
        }

        response_text = ""

        # Stream the response and catch tool calls
        for chunk in agent_executor.stream(
            {"messages": [HumanMessage(content=str(user_message))]}, 
            config
        ):
            if 'agent' in chunk and 'messages' in chunk['agent']:
                for message in chunk['agent']['messages']:
                    if isinstance(message, AIMessage):
                        # Handle tool calls
                        if hasattr(message, 'tool_calls') and message.tool_calls:
                            for tool_call in message.tool_calls:
                                if tool_call['name'] == "AlarmManager":
                                    # Convert user_id to string
                                    tool_call['args']["user_id"] = user_id_str
                                    # print("AlarmManager tool called --> ", tool_call['args'])

                                    # Convert ObjectId fields to string for serialization
                                    if "filter" in tool_call['args']["query"]:
                                        if "_id" in tool_call['args']["query"]["filter"]:
                                            tool_call['args']["query"]["filter"]["_id"] = str(tool_call['args']["query"]["filter"]["_id"])
                                        tool_call['args']["query"]["filter"]["user_id"] = user_id_str

                                elif tool_call['name'] == "TaskManager":
                                    # Convert user_id to string
                                    tool_call['args']["user_id"] = user_id_str
                                    # print("TaskManager tool called --> ", tool_call['args'])

                                    # Convert ObjectId fields to string for serialization
                                    if "_id" in tool_call['args']["query"]:
                                        tool_call['args']["query"]["_id"] = str(tool_call['args']["query"]["_id"])

                                    if "filter" in tool_call['args']["query"]:
                                        if "_id" in tool_call['args']["query"]["filter"]:
                                            tool_call['args']["query"]["filter"]["_id"] = str(tool_call['args']["query"]["filter"]["_id"])
                                        if "subtasks._id" in tool_call['args']["query"]["filter"]:
                                            tool_call['args']["query"]["filter"]["subtasks._id"] = str(tool_call['args']["query"]["filter"]["subtasks._id"])
                                        tool_call['args']["query"]["filter"]["user_id"] = user_id_str

                        # Handle the actual response content
                        elif message.content:
                            response_text = convert_objectid_to_str(message.content)

        # Store messages
        message = Message(
            sender="User",
            message=user_message,
            timestamp=datetime.datetime.now(datetime.UTC).isoformat()
        ) 

        bot_message = Message(
            sender="Bot",
            message=response_text,
            timestamp=datetime.datetime.now(datetime.UTC).isoformat()
        )

        message_entries = [message.model_dump(), bot_message.model_dump()]
        memory.store_messages(user_id=user_id, message_entries=message_entries)
        return response_text
    
    except Exception as e:
        if "429" in str(e):
            return (
                "It seems you've exceeded your current quota for API usage.\n"
                "Please check your plan and billing details on the [OpenAI Billing Dashboard](https://platform.openai.com/account/billing/overview).\n\n"
                "To update your API key or settings, visit the [ChinniAI Settings Page](https://chinni-ai.vercel.app/settings)."
            )
        if "api_key" in str(e):
            return "It looks like you haven't set your OpenAI API key yet.\nPlease follow these steps to get started:\n1. **Get your API key**\nVisit the [OpenAI website](https://platform.openai.com/account/api-keys) to generate your API key.\n\n2. **Set the API key**\nGo to the [settings page](https://chinni-ai.vercel.app/settings) of ChinniAI Assistant and enter your API key.\n\nOnce you've set your API key, you're ready to use ChinniAI Assistant!"
        
        return "Something went wrong please try again later..."

