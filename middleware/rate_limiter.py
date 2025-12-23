"""
Rate Limiter - защита от спама
"""
from datetime import datetime, timedelta
from collections import defaultdict
import config

# In-memory хранилище для rate limiting
user_requests = defaultdict(list)
user_hourly_requests = defaultdict(list)


def check_rate_limit(vk_id):
    """
    Проверка rate limit для пользователя
    Возвращает (allowed, wait_time)
    """
    now = datetime.now()
    
    # Очистка старых запросов (старше RATE_LIMIT_SECONDS)
    cutoff_time = now - timedelta(seconds=config.RATE_LIMIT_SECONDS)
    user_requests[vk_id] = [t for t in user_requests[vk_id] if t > cutoff_time]
    
    # Проверка лимита по секундам
    if len(user_requests[vk_id]) >= 1:
        wait_time = config.RATE_LIMIT_SECONDS - (now - user_requests[vk_id][0]).total_seconds()
        return False, max(0, wait_time)
    
    # Добавление текущего запроса
    user_requests[vk_id].append(now)
    return True, 0


def check_hourly_limit(vk_id, limit=None):
    """
    Проверка часового лимита запросов (для покупок)
    Возвращает (allowed, remaining_requests)
    """
    if limit is None:
        limit = config.MAX_REQUESTS_PER_HOUR
    
    now = datetime.now()
    
    # Очистка старых запросов (старше 1 часа)
    cutoff_time = now - timedelta(hours=1)
    user_hourly_requests[vk_id] = [t for t in user_hourly_requests[vk_id] if t > cutoff_time]
    
    # Проверка лимита
    if len(user_hourly_requests[vk_id]) >= limit:
        return False, 0
    
    # Добавление текущего запроса
    user_hourly_requests[vk_id].append(now)
    remaining = limit - len(user_hourly_requests[vk_id])
    return True, remaining


def rate_limit(func):
    """Декоратор для проверки rate limit"""
    def wrapper(vk, event, session, *args, **kwargs):
        allowed, wait_time = check_rate_limit(event.user_id)
        
        if not allowed:
            vk.messages.send(
                user_id=event.user_id,
                message=f"⏳ Подождите {int(wait_time)} сек. перед следующей командой",
                random_id=0
            )
            return
        
        return func(vk, event, session, *args, **kwargs)
    return wrapper


def hourly_limit(func):
    """Декоратор для проверки часового лимита"""
    def wrapper(vk, event, session, *args, **kwargs):
        allowed, remaining = check_hourly_limit(event.user_id)
        
        if not allowed:
            vk.messages.send(
                user_id=event.user_id,
                message=f"⏰ Вы достигли лимита запросов ({config.MAX_REQUESTS_PER_HOUR}/час). Попробуйте позже.",
                random_id=0
            )
            return
        
        return func(vk, event, session, *args, **kwargs)
    return wrapper