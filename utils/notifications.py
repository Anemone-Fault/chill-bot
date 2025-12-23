"""
Система уведомлений
"""
from database.queries import get_player_by_vk_id
from utils.formatters import format_balance


def send_notification(vk, vk_id, message, keyboard=None):
    """Отправить уведомление игроку (если у него включены уведомления)"""
    try:
        vk.messages.send(
            user_id=vk_id,
            message=message,
            keyboard=keyboard,
            random_id=0
        )
        return True
    except Exception as e:
        print(f"❌ Ошибка отправки уведомления {vk_id}: {e}")
        return False


def notify_transfer_received(vk, session, receiver_vk_id, sender_name, amount, is_anonymous=False):
    """Уведомление о получении перевода"""
    receiver = get_player_by_vk_id(session, receiver_vk_id)
    
    if not receiver or not receiver.notifications_enabled:
        return False
    
    if is_anonymous:
        sender_text = "Анонимный игрок"
    else:
        sender_text = sender_name
    
    message = f"💸 Вам перевели {format_balance(amount)} чилликов!\n"
    message += f"От: {sender_text}\n"
    message += f"💰 Ваш баланс: {format_balance(receiver.balance)} чил."
    
    return send_notification(vk, receiver_vk_id, message)


def notify_purchase_approved(vk, session, player_vk_id, item_name, price):
    """Уведомление об одобрении покупки"""
    player = get_player_by_vk_id(session, player_vk_id)
    
    if not player or not player.notifications_enabled:
        return False
    
    message = f"✅ Ваш запрос на '{item_name}' одобрен!\n"
    message += f"💰 Стоимость: {format_balance(price)} чилликов\n"
    message += f"💳 Списано с баланса: {format_balance(price)} чил.\n"
    message += f"Остаток: {format_balance(player.balance)} чил."
    
    return send_notification(vk, player_vk_id, message)


def notify_purchase_rejected(vk, session, player_vk_id, item_name, reason):
    """Уведомление об отклонении покупки"""
    player = get_player_by_vk_id(session, player_vk_id)
    
    if not player or not player.notifications_enabled:
        return False
    
    message = f"❌ Ваш запрос на '{item_name}' отклонён\n"
    if reason:
        message += f"Причина: {reason}"
    
    return send_notification(vk, player_vk_id, message)


def notify_admin_operation(vk, session, player_vk_id, operation_type, amount, reason=None):
    """Уведомление об операции администратора"""
    player = get_player_by_vk_id(session, player_vk_id)
    
    if not player or not player.notifications_enabled:
        return False
    
    if operation_type == 'give':
        message = f"💰 Администратор начислил вам {format_balance(amount)} чилликов!\n"
    else:
        message = f"💳 Администратор списал у вас {format_balance(amount)} чилликов\n"
    
    if reason:
        message += f"Причина: {reason}\n"
    
    message += f"💰 Ваш баланс: {format_balance(player.balance)} чил."
    
    return send_notification(vk, player_vk_id, message)


def notify_scheduled_payment(vk, session, player_vk_id, amount, reason=None):
    """Уведомление о запланированном начислении"""
    player = get_player_by_vk_id(session, player_vk_id)
    
    if not player or not player.notifications_enabled:
        return False
    
    message = f"⏰ Вам начислено {format_balance(amount)} чилликов!\n"
    if reason:
        message += f"💬 {reason}\n"
    message += f"💰 Ваш баланс: {format_balance(player.balance)} чил."
    
    return send_notification(vk, player_vk_id, message)


def notify_ban(vk, vk_id, reason=None):
    """Уведомление о блокировке"""
    message = "🚫 Вы заблокированы в боте!"
    if reason:
        message += f"\nПричина: {reason}"
    
    return send_notification(vk, vk_id, message)


def notify_unban(vk, vk_id):
    """Уведомление о разблокировке"""
    message = "✅ Ваша блокировка снята! Вы снова можете пользоваться ботом."
    return send_notification(vk, vk_id, message)