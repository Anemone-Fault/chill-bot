"""
Система достижений
"""
from database.queries import add_achievement, get_player_transactions
from database.models import TransactionType
from utils.formatters import format_achievement_earned
from utils.notifications import send_notification


# Определение достижений
ACHIEVEMENTS = {
    'first_purchase': {
        'title': 'Первая покупка',
        'description': 'Совершили первую покупку',
        'icon': '🏆'
    },
    'generous': {
        'title': 'Щедрость',
        'description': 'Перевели более 1000 чилликов',
        'icon': '💸'
    },
    'accumulator': {
        'title': 'Накопитель',
        'description': 'Достигли 500 чилликов на балансе',
        'icon': '🔥'
    },
    'activist': {
        'title': 'Активист',
        'description': 'Совершили 100 транзакций',
        'icon': '⚡'
    },
    'rich': {
        'title': 'Богач',
        'description': 'Достигли 1000 чилликов на балансе',
        'icon': '💎'
    },
    'mega_generous': {
        'title': 'Мега-щедрость',
        'description': 'Перевели более 5000 чилликов',
        'icon': '🌟'
    }
}


def check_achievements(session, vk, player):
    """
    Проверка и начисление достижений
    Возвращает список новых достижений
    """
    new_achievements = []
    
    # Получение транзакций игрока
    transactions = get_player_transactions(session, player.id, limit=1000)
    
    # Подсчёт статистики
    total_transfers = sum(t.amount for t in transactions if t.type == TransactionType.TRANSFER and t.from_player_id == player.id)
    total_purchases = len([t for t in transactions if t.type == TransactionType.PURCHASE])
    total_transactions_count = len(transactions)
    
    # Проверка достижений
    
    # Первая покупка
    if total_purchases >= 1:
        ach = add_achievement(
            session,
            player.id,
            'first_purchase',
            ACHIEVEMENTS['first_purchase']['title'],
            ACHIEVEMENTS['first_purchase']['description'],
            ACHIEVEMENTS['first_purchase']['icon']
        )
        if ach:
            new_achievements.append(ach)
    
    # Щедрость (1000+ переводов)
    if total_transfers >= 1000:
        ach = add_achievement(
            session,
            player.id,
            'generous',
            ACHIEVEMENTS['generous']['title'],
            ACHIEVEMENTS['generous']['description'],
            ACHIEVEMENTS['generous']['icon']
        )
        if ach:
            new_achievements.append(ach)
    
    # Мега-щедрость (5000+ переводов)
    if total_transfers >= 5000:
        ach = add_achievement(
            session,
            player.id,
            'mega_generous',
            ACHIEVEMENTS['mega_generous']['title'],
            ACHIEVEMENTS['mega_generous']['description'],
            ACHIEVEMENTS['mega_generous']['icon']
        )
        if ach:
            new_achievements.append(ach)
    
    # Накопитель (500+ баланс)
    if player.balance >= 500:
        ach = add_achievement(
            session,
            player.id,
            'accumulator',
            ACHIEVEMENTS['accumulator']['title'],
            ACHIEVEMENTS['accumulator']['description'],
            ACHIEVEMENTS['accumulator']['icon']
        )
        if ach:
            new_achievements.append(ach)
    
    # Богач (1000+ баланс)
    if player.balance >= 1000:
        ach = add_achievement(
            session,
            player.id,
            'rich',
            ACHIEVEMENTS['rich']['title'],
            ACHIEVEMENTS['rich']['description'],
            ACHIEVEMENTS['rich']['icon']
        )
        if ach:
            new_achievements.append(ach)
    
    # Активист (100+ транзакций)
    if total_transactions_count >= 100:
        ach = add_achievement(
            session,
            player.id,
            'activist',
            ACHIEVEMENTS['activist']['title'],
            ACHIEVEMENTS['activist']['description'],
            ACHIEVEMENTS['activist']['icon']
        )
        if ach:
            new_achievements.append(ach)
    
    # Отправка уведомлений о новых достижениях
    for ach in new_achievements:
        msg = format_achievement_earned(ach)
        send_notification(vk, player.vk_id, msg)
    
    return new_achievements