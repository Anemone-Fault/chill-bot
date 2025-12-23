"""
Middleware для проверки прав доступа
"""
import config
from database.queries import get_player_by_vk_id


def is_admin(vk_id):
    """Проверка, является ли пользователь администратором"""
    return vk_id in config.ADMIN_IDS


def check_player_banned(session, vk_id):
    """Проверка, заблокирован ли игрок"""
    player = get_player_by_vk_id(session, vk_id)
    if player and player.is_banned:
        return True, player.ban_reason
    return False, None


def require_admin(func):
    """Декоратор для проверки прав администратора"""
    def wrapper(vk, event, session, *args, **kwargs):
        if not is_admin(event.user_id):
            vk.messages.send(
                user_id=event.user_id,
                message="❌ У вас нет прав администратора!",
                random_id=0
            )
            return
        return func(vk, event, session, *args, **kwargs)
    return wrapper


def require_not_banned(func):
    """Декоратор для проверки блокировки игрока"""
    def wrapper(vk, event, session, *args, **kwargs):
        is_banned, reason = check_player_banned(session, event.user_id)
        if is_banned:
            msg = f"🚫 Вы заблокированы!"
            if reason:
                msg += f"\nПричина: {reason}"
            vk.messages.send(
                user_id=event.user_id,
                message=msg,
                random_id=0
            )
            return
        return func(vk, event, session, *args, **kwargs)
    return wrapper