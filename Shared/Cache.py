from main import message_cache, deleted_cache, edited_cache, bot_error_cache
from datetime import datetime, timedelta

def clean_cache():
    global message_cache, deleted_cache, edited_cache, bot_error_cache
    now = datetime.now()
    message_cache = [m for m in message_cache if now - m['time'] < timedelta(minutes=120)]
    deleted_cache = [m for m in deleted_cache if now - m['time'] < timedelta(minutes=120)]
    edited_cache = [m for m in edited_cache if now - m['time'] < timedelta(minutes=120)]
    bot_error_cache = [m for m in bot_error_cache if now - m['time'] < timedelta(minutes=120)]