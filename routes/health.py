from fastapi import APIRouter, HTTPException
from datetime import datetime

router = APIRouter()

# Global variable to track last cron execution
last_cron_check = datetime.now()

def update_last_check():
    """Update the last check timestamp"""
    global last_cron_check
    last_cron_check = datetime.now()

@router.get("/cron-status")
async def check_cron_status():
    """Check if the cron job is running properly"""
    global last_cron_check
    
    # Calculate time difference
    time_diff = (datetime.now() - last_cron_check).total_seconds()
    
    if time_diff > 5:  # If more than 5 seconds have passed
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Cron job may be stuck or not running",
                "last_check": last_cron_check.isoformat(),
                "seconds_since_last_check": time_diff
            }
        )
    
    return {
        "status": "healthy",
        "last_check": last_cron_check.isoformat(),
        "seconds_since_last_check": time_diff
    } 