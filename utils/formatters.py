"""
Форматирование сообщений
"""
from datetime import datetime


def format_balance(balance):
    """Форматирование баланса с разделителями"""
    return f"{balance:,}".replace(',', ' ')


def format_transaction_type(transaction_type):
    """Форматирование типа транзакции"""
    types = {
        'transfer': '➡️ Перевод',
        'purchase': '🛒 Покупка',
        'admin_give': '💰 Начисление админом',
        'admin_take': '💳 Списание админом',
        'scheduled_give': '⏰ Запланированное начисление'
    }
    return types.get(transaction_type, '❓ Неизвестно')


def format_datetime(dt):
    """Форматирование даты и времени"""
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    return dt.strftime('%d.%m.%Y %H:%M')


def format_player_profile(player, include_achievements=False, achievements=None):
    """Форматирование профиля игрока"""
    msg = f"👤 Профиль: {player.first_name} {player.last_name}\n"
    msg += f"🆔 VK ID: {player.vk_id}\n"
    msg += f"💰 Баланс: {format_balance(player.balance)} чилликов\n"
    msg += f"⭐ Уровень: {player.level}\n"
    msg += f"✨ Опыт: {format_balance(player.experience)} XP\n"
    msg += f"💬 Сообщений: {format_balance(player.messages_count)}\n"
    msg += f"📅 Регистрация: {format_datetime(player.created_at)}\n"
    
    if include_achievements and achievements:
        msg += f"\n🏆 Достижения ({len(achievements)}):\n"
        for ach in achievements[:5]:  # Показываем первые 5
            msg += f"{ach.icon} {ach.title}\n"
        if len(achievements) > 5:
            msg += f"... и ещё {len(achievements) - 5}\n"
    
    return msg


def format_transaction_history(transactions, player_id):
    """Форматирование истории транзакций"""
    if not transactions:
        return "📋 История транзакций пуста"
    
    msg = "📜 История последних операций:\n\n"
    
    for t in transactions:
        date = format_datetime(t.created_at)
        amount = t.amount
        
        # Определяем направление операции
        if t.from_player_id == player_id:
            direction = f"➖ -{amount}"
        elif t.to_player_id == player_id:
            direction = f"➕ +{amount}"
        else:
            direction = f"💰 {amount}"
        
        type_str = format_transaction_type(t.type.value if hasattr(t.type, 'value') else t.type)
        
        msg += f"{type_str}\n"
        msg += f"   {direction} чил. • {date}\n"
        
        if t.reason:
            msg += f"   💬 {t.reason}\n"
        
        msg += "\n"
    
    return msg.strip()


def format_leaderboard(players):
    """Форматирование таблицы лидеров"""
    if not players:
        return "🏆 Таблица лидеров пуста"
    
    msg = "🏆 Топ игроков по балансу:\n\n"
    
    medals = ['🥇', '🥈', '🥉']
    
    for i, player in enumerate(players, 1):
        medal = medals[i-1] if i <= 3 else f"{i}."
        name = f"{player.first_name} {player.last_name}"
        balance = format_balance(player.balance)
        
        msg += f"{medal} {name} — {balance} чил.\n"
    
    return msg


def format_stats(stats_dict):
    """Форматирование статистики"""
    msg = "📊 Статистика:\n\n"
    
    for key, value in stats_dict.items():
        if isinstance(value, (int, float)):
            value = format_balance(int(value))
        msg += f"• {key}: {value}\n"
    
    return msg


def format_achievement_earned(achievement):
    """Форматирование уведомления о новом достижении"""
    msg = f"🎉 Получено новое достижение!\n\n"
    msg += f"{achievement.icon} {achievement.title}\n"
    if achievement.description:
        msg += f"{achievement.description}\n"
    return msg


def format_level_up(new_level):
    """Форматирование уведомления о повышении уровня"""
    return f"🎊 Поздравляем! Вы достигли {new_level} уровня!"