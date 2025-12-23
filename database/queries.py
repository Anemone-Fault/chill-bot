"""
Готовые запросы к базе данных
"""
from sqlalchemy import desc, func
from database.models import Player, Transaction, PurchaseRequest, Achievement, ScheduledPayment
from datetime import datetime, timedelta
import config


def get_or_create_player(session, vk_id, first_name, last_name):
    """Получить или создать игрока"""
    player = session.query(Player).filter_by(vk_id=vk_id).first()
    
    if not player:
        player = Player(
            vk_id=vk_id,
            first_name=first_name,
            last_name=last_name,
            balance=config.STARTING_BALANCE
        )
        session.add(player)
        session.commit()
        print(f"✅ Создан новый игрок: {first_name} {last_name} (VK ID: {vk_id})")
    
    return player


def get_player_by_vk_id(session, vk_id):
    """Получить игрока по VK ID"""
    return session.query(Player).filter_by(vk_id=vk_id).first()


def update_player_balance(session, player_id, new_balance):
    """Обновить баланс игрока"""
    player = session.query(Player).filter_by(id=player_id).first()
    if player:
        player.balance = new_balance
        session.commit()
        return True
    return False


def create_transaction(session, from_player_id, to_player_id, amount, transaction_type, reason=None, is_anonymous=False):
    """Создать транзакцию"""
    transaction = Transaction(
        from_player_id=from_player_id,
        to_player_id=to_player_id,
        amount=amount,
        type=transaction_type,
        reason=reason,
        is_anonymous=is_anonymous
    )
    session.add(transaction)
    session.commit()
    return transaction


def get_player_transactions(session, player_id, limit=10, transaction_filter=None):
    """Получить транзакции игрока с фильтром"""
    query = session.query(Transaction).filter(
        (Transaction.from_player_id == player_id) | (Transaction.to_player_id == player_id)
    )
    
    # Применение фильтра
    if transaction_filter == 'переводы':
        query = query.filter(Transaction.type == 'transfer')
    elif transaction_filter == 'покупки':
        query = query.filter(Transaction.type == 'purchase')
    elif transaction_filter == 'админ':
        query = query.filter(Transaction.type.in_(['admin_give', 'admin_take']))
    
    return query.order_by(desc(Transaction.created_at)).limit(limit).all()


def get_top_players(session, limit=10, include_hidden=False):
    """Получить топ игроков по балансу"""
    query = session.query(Player).filter(Player.is_banned == False)
    
    if not include_hidden:
        query = query.filter(Player.hide_balance == False)
    
    return query.order_by(desc(Player.balance)).limit(limit).all()


def create_purchase_request(session, player_id, item_description):
    """Создать запрос на покупку"""
    request = PurchaseRequest(
        player_id=player_id,
        item_description=item_description,
        status='pending'
    )
    session.add(request)
    session.commit()
    return request


def get_pending_purchase_requests(session):
    """Получить все ожидающие запросы"""
    return session.query(PurchaseRequest).filter_by(status='pending').all()


def add_achievement(session, player_id, achievement_type, title, description, icon):
    """Добавить достижение игроку"""
    # Проверка, есть ли уже такое достижение
    existing = session.query(Achievement).filter_by(
        player_id=player_id,
        achievement_type=achievement_type
    ).first()
    
    if existing:
        return None  # Достижение уже есть
    
    achievement = Achievement(
        player_id=player_id,
        achievement_type=achievement_type,
        title=title,
        description=description,
        icon=icon
    )
    session.add(achievement)
    session.commit()
    return achievement


def get_player_achievements(session, player_id):
    """Получить все достижения игрока"""
    return session.query(Achievement).filter_by(player_id=player_id).all()


def increment_message_count(session, player_id):
    """Увеличить счётчик сообщений игрока (для опыта)"""
    player = session.query(Player).filter_by(id=player_id).first()
    if player:
        player.messages_count += 1
        player.experience += 10  # 10 XP за сообщение
        
        # Расчёт уровня (простая формула: 100 XP на уровень)
        new_level = (player.experience // 100) + 1
        if new_level > player.level:
            player.level = new_level
            session.commit()
            return True, new_level  # Уровень повышен
        
        session.commit()
        return False, player.level
    return False, 1


def get_global_stats(session):
    """Получить глобальную статистику"""
    total_players = session.query(func.count(Player.id)).scalar()
    total_emission = session.query(func.sum(Player.balance)).scalar() or 0
    avg_balance = session.query(func.avg(Player.balance)).scalar() or 0
    total_transactions = session.query(func.count(Transaction.id)).scalar()
    
    return {
        'total_players': total_players,
        'total_emission': total_emission,
        'avg_balance': round(avg_balance, 2),
        'total_transactions': total_transactions
    }


def ban_player(session, vk_id, reason=None):
    """Заблокировать игрока"""
    player = get_player_by_vk_id(session, vk_id)
    if player:
        player.is_banned = True
        player.ban_reason = reason
        session.commit()
        return True
    return False


def unban_player(session, vk_id):
    """Разблокировать игрока"""
    player = get_player_by_vk_id(session, vk_id)
    if player:
        player.is_banned = False
        player.ban_reason = None
        session.commit()
        return True
    return False


def delete_player(session, vk_id):
    """Удалить игрока и все его данные"""
    player = get_player_by_vk_id(session, vk_id)
    if player:
        # Удаление связанных записей
        session.query(Transaction).filter(
            (Transaction.from_player_id == player.id) | (Transaction.to_player_id == player.id)
        ).delete()
        session.query(PurchaseRequest).filter_by(player_id=player.id).delete()
        session.query(Achievement).filter_by(player_id=player.id).delete()
        session.query(ScheduledPayment).filter_by(player_id=player.id).delete()
        
        # Удаление самого игрока
        session.delete(player)
        session.commit()
        return True
    return False


def create_scheduled_payment(session, player_id, admin_id, amount, scheduled_for, reason=None):
    """Создать запланированное начисление"""
    payment = ScheduledPayment(
        player_id=player_id,
        admin_id=admin_id,
        amount=amount,
        scheduled_for=scheduled_for,
        reason=reason
    )
    session.add(payment)
    session.commit()
    return payment


def get_due_scheduled_payments(session):
    """Получить все платежи, которые должны быть выполнены"""
    now = datetime.now()
    return session.query(ScheduledPayment).filter(
        ScheduledPayment.scheduled_for <= now,
        ScheduledPayment.executed == False
    ).all()


def mark_payment_executed(session, payment_id):
    """Отметить платёж как выполненный"""
    payment = session.query(ScheduledPayment).filter_by(id=payment_id).first()
    if payment:
        payment.executed = True
        payment.executed_at = datetime.now()
        session.commit()
        return True
    return False