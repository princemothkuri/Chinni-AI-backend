from datetime import datetime
from zoneinfo import ZoneInfo

def convert_to_iso(alarm_time_str: str) -> str:
    """Convert date string to ISO format with IST timezone"""
    alarm_time_parsed = datetime.strptime(alarm_time_str, "%d %B, %I:%M %p %Y")
    alarm_time_with_timezone = alarm_time_parsed.replace(tzinfo=ZoneInfo("Asia/Kolkata"))
    return alarm_time_with_timezone.isoformat()

def convert_from_iso(iso_time_str: str) -> str:
    """Convert ISO format to readable date string"""
    iso_datetime = datetime.fromisoformat(iso_time_str)
    return iso_datetime.strftime("%d %B, %I:%M %p %Y")
