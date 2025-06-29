import time
import datetime

def current_time():
    """Returns current time in human-readable format"""
    return time.strftime("%Y-%m-%d %H:%M:%S")

def timestamp():
    """Returns raw timestamp"""
    return time.time()

def sleep(seconds):
    """Sleep for specified seconds"""
    time.sleep(seconds)

def future_date(days=0):
    """Get future date as string (YYYY-MM-DD)"""
    date = datetime.datetime.now() + datetime.timedelta(days=days)
    return date.strftime("%Y-%m-%d")

def timezone():
    """Get current timezone information"""
    return time.tzname

def day_of_week():
    """Get current day name"""
    return datetime.datetime.now().strftime("%A")

def formatted_time(fmt="%H:%M:%S"):
    """Returns custom formatted time string"""
    return time.strftime(fmt)
