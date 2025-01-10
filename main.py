from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import auth, user, ai, health, alarm, tasks, settings  # Import the tasks router
from sockets import setup_websocket
from cronjobs.alarm_notifications import start_alarm_cron
from cronjobs.task_notifications import start_task_cron
from contextlib import asynccontextmanager
import asyncio
from config import FRONTEND_URL
from dotenv import load_dotenv

# Load .env variables into the environment
load_dotenv()

# Store the tasks globally
alarm_cron_task = None
task_cron_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create the background tasks
    global alarm_cron_task, task_cron_task
    alarm_cron_task = asyncio.create_task(start_alarm_cron())
    task_cron_task = asyncio.create_task(start_task_cron())
    
    yield  # This is where FastAPI runs
    
    # Shutdown: Cancel the background tasks
    if alarm_cron_task:
        alarm_cron_task.cancel()
        try:
            await alarm_cron_task
        except asyncio.CancelledError:
            print("Alarm cron job cancelled")
            
    if task_cron_task:
        task_cron_task.cancel()
        try:
            await task_cron_task
        except asyncio.CancelledError:
            print("Task cron job cancelled")

def create_app():
    app = FastAPI(title="ChinniAI Backend", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[FRONTEND_URL],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include all API routes
    app.include_router(auth.router, prefix="/auth", tags=["Auth"])
    app.include_router(user.router, prefix="/user", tags=["User"])
    app.include_router(ai.router, prefix="/ai", tags=["AI"])
    app.include_router(settings.router, prefix="/settings", tags=["Settings"])
    app.include_router(health.router, prefix="/health", tags=["Health"])
    app.include_router(alarm.router, prefix="/api")
    app.include_router(tasks.router, prefix="/api")

    # Setup WebSocket
    setup_websocket(app)
    
    # Default route to check if the backend is running
    @app.get("/")
    async def read_root():
        return {"message": "ChinniAI backend is running"}

    return app

if __name__ == '__main__':
    import uvicorn
    uvicorn.run("main:create_app", host="0.0.0.0", port=8000, reload=True)