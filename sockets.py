from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from utils.jwt_handler import verify_token
from utils.agent import chinniAiAgent
from database.database import users_collection
from bson import ObjectId
import json
from cronjobs.websocket_store import register_websocket, remove_websocket

def setup_websocket(app: FastAPI):
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        auth_token = websocket.query_params.get("authToken")
        user_id = verify_token(auth_token)

        if not user_id:
            await websocket.close(code=1008)  # Policy Violation
            # print("Connection rejected: Invalid auth token")
            return

        await websocket.accept()
        
        socket_id = str(websocket.client.port)
        
        # Store WebSocket connection ID in database
        users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"socket_id": socket_id}}
        )
        
        # Register WebSocket connection
        register_websocket(socket_id, websocket)
        
        # print(f"User {user_id} connected with socket {socket_id}")

        try:
            while True:
                data = await websocket.receive_text()
                # print(f"Received message from {user_id}")
                
                try:
                    # Convert user_id to ObjectId for MongoDB
                    user_object_id = ObjectId(user_id)
                    
                    # Get response from ChinniAI
                    ai_response = chinniAiAgent(data, user_object_id)
                    
                    # Send response back to user
                    response_data = {
                        "type": "ai_response",
                        "message": ai_response
                    }
                    await websocket.send_text(json.dumps(response_data))
                    
                except Exception as e:
                    error_response = {
                        "type": "error",
                        "message": f"Error processing message: {str(e)}"
                    }
                    await websocket.send_text(json.dumps(error_response))
                    
        except WebSocketDisconnect:
            # Remove socket_id when user disconnects
            users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$unset": {"socket_id": ""}}
            )
            # Remove WebSocket connection
            remove_websocket(socket_id)
            # print(f"User {user_id} disconnected")
