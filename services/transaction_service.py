"""
Бизнес-логика транзакций
"""
from database.models import TransactionType
from database.queries import (
    get_player_by_vk_id,
    update_player_balance,
    create_transaction
)
from utils.notifications import notify_transfer_received, notify_admin_operation


def transfer_chilliki(session, vk, sender_vk_id, receiver_vk_id, amount, is_anonymous=False):
    """
    Перевод чилликов между игроками
    Возвращает (success, message)
    """
    # Получение игроков
    sender = get_player_by_vk_id(session, sender_vk_id)
    receiver = get_player_by_vk_id(session, receiver_vk_id)
    
    if not sender:
        return False, "❌ Ваш профиль не найден"
    
    if not receiver:
        return False, "❌ Профиль получателя не найден"
    
    if sender.id == receiver.id:
        return False, "❌ Нельзя переводить чиллики самому себе"
    
    # Проверка баланса
    if sender.balance < amount:
        return False, f"❌ Недостаточно чилликов!\nВаш баланс: {sender.balance}, требуется: {amount}"
    
    # Выполнение перевода
    try:
        sender.balance -= amount
        receiver.balance += amount
        
        # Создание транзакции
        create_transaction(
            session,
            from_player_id=sender.id,
            to_player_id=receiver.id,
            amount=amount,
            transaction_type=TransactionType.TRANSFER,
            is_anonymous=is_anonymous
        )
        
        # Уведомление получателя
        sender_name = f"{sender.first_name} {sender.last_name}"
        notify_transfer_received(vk, session, receiver_vk_id, sender_name, amount, is_anonymous)
        
        return True, f"✅ Перевод выполнен!\n💸 Переведено: {amount} чил.\n💰 Ваш баланс: {sender.balance} чил."
    
    except Exception as e:
        session.rollback()
        return False, f"❌ Ошибка при переводе: {e}"


def admin_give_chilliki(session, vk, admin_vk_id, player_vk_id, amount, reason=None):
    """
    Начисление чилликов администратором
    Возвращает (success, message)
    """
    player = get_player_by_vk_id(session, player_vk_id)
    
    if not player:
        return False, "❌ Профиль игрока не найден"
    
    try:
        player.balance += amount
        
        # Создание транзакции
        create_transaction(
            session,
            from_player_id=None,  # NULL для админских начислений
            to_player_id=player.id,
            amount=amount,
            transaction_type=TransactionType.ADMIN_GIVE,
            reason=reason
        )
        
        # Уведомление игрока
        notify_admin_operation(vk, session, player_vk_id, 'give', amount, reason)
        
        return True, f"✅ Начислено {amount} чилликов игроку {player.first_name} {player.last_name}\n💰 Его баланс: {player.balance} чил."
    
    except Exception as e:
        session.rollback()
        return False, f"❌ Ошибка при начислении: {e}"


def admin_take_chilliki(session, vk, admin_vk_id, player_vk_id, amount, reason=None):
    """
    Списание чилликов администратором
    Возвращает (success, message)
    """
    player = get_player_by_vk_id(session, player_vk_id)
    
    if not player:
        return False, "❌ Профиль игрока не найден"
    
    if player.balance < amount:
        return False, f"❌ У игрока недостаточно чилликов!\nБаланс: {player.balance}, требуется: {amount}"
    
    try:
        player.balance -= amount
        
        # Создание транзакции
        create_transaction(
            session,
            from_player_id=player.id,
            to_player_id=None,  # NULL для админских списаний
            amount=amount,
            transaction_type=TransactionType.ADMIN_TAKE,
            reason=reason
        )
        
        # Уведомление игрока
        notify_admin_operation(vk, session, player_vk_id, 'take', amount, reason)
        
        return True, f"✅ Списано {amount} чилликов у игрока {player.first_name} {player.last_name}\n💰 Его баланс: {player.balance} чил."
    
    except Exception as e:
        session.rollback()
        return False, f"❌ Ошибка при списании: {e}"


def purchase_item(session, vk, player_vk_id, item_name, price):
    """
    Покупка предмета/способности
    Возвращает (success, message)
    """
    player = get_player_by_vk_id(session, player_vk_id)
    
    if not player:
        return False, "❌ Ваш профиль не найден"
    
    if player.balance < price:
        return False, f"❌ Недостаточно чилликов!\nВаш баланс: {player.balance}, требуется: {price}"
    
    try:
        player.balance -= price
        
        # Создание транзакции
        create_transaction(
            session,
            from_player_id=player.id,
            to_player_id=None,
            amount=price,
            transaction_type=TransactionType.PURCHASE,
            reason=item_name
        )
        
        return True, f"✅ Покупка '{item_name}' завершена!\n💳 Списано: {price} чил.\n💰 Ваш баланс: {player.balance} чил."
    
    except Exception as e:
        session.rollback()
        return False, f"❌ Ошибка при покупке: {e}"