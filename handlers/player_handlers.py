"""
Обработчики команд игрока
"""
from database.queries import (
    get_player_by_vk_id,
    get_player_transactions,
    get_top_players,
    get_player_achievements,
    get_global_stats
)
from keyboards.vk_keyboards import (
    get_main_menu_keyboard,
    get_confirmation_keyboard,
    get_amount_keyboard,
    get_history_filter_keyboard,
    get_settings_keyboard
)
from utils.formatters import (
    format_player_profile,
    format_transaction_history,
    format_leaderboard,
    format_balance
)
from utils.validators import validate_amount, validate_vk_id
from services.transaction_service import transfer_chilliki
from services.achievement_service import check_achievements
from middleware.auth import require_not_banned
from middleware.rate_limiter import rate_limit
import states


@require_not_banned
@rate_limit
def handle_balance(vk, event, session):
    """Просмотр баланса и профиля"""
    player = get_player_by_vk_id(session, event.user_id)
    
    if not player:
        vk.messages.send(
            user_id=event.user_id,
            message="❌ Профиль не найден. Используйте /start",
            random_id=0
        )
        return
    
    # Получение достижений
    achievements = get_player_achievements(session, player.id)
    
    # Форматирование профиля
    profile_msg = format_player_profile(player, include_achievements=True, achievements=achievements)
    
    vk.messages.send(
        user_id=event.user_id,
        message=profile_msg,
        keyboard=get_main_menu_keyboard(),
        random_id=0
    )


@require_not_banned
@rate_limit
def handle_transfer_start(vk, event, session):
    """Начало процесса перевода"""
    states.set_state(event.user_id, states.State.WAITING_RECEIVER)
    
    vk.messages.send(
        user_id=event.user_id,
        message="➡️ Перевод чилликов\n\nУкажите получателя (VK ID, @id123 или ссылку):",
        random_id=0
    )


@require_not_banned
def handle_transfer_receiver(vk, event, session, receiver_input):
    """Обработка получателя перевода"""
    # Валидация VK ID
    valid, receiver_vk_id, error = validate_vk_id(receiver_input)
    
    if not valid:
        vk.messages.send(
            user_id=event.user_id,
            message=f"❌ {error}",
            random_id=0
        )
        return
    
    # Проверка существования получателя
    receiver = get_player_by_vk_id(session, receiver_vk_id)
    if not receiver:
        vk.messages.send(
            user_id=event.user_id,
            message=f"❌ Игрок с ID {receiver_vk_id} не найден в системе",
            random_id=0
        )
        return
    
    # Обновление состояния
    states.update_state_data(event.user_id, receiver_vk_id=receiver_vk_id)
    states.set_state(event.user_id, states.State.WAITING_TRANSFER_AMOUNT, receiver_vk_id=receiver_vk_id)
    
    vk.messages.send(
        user_id=event.user_id,
        message=f"✅ Получатель: {receiver.first_name} {receiver.last_name}\n\nУкажите сумму для перевода:",
        keyboard=get_amount_keyboard(),
        random_id=0
    )


@require_not_banned
def handle_transfer_amount(vk, event, session, amount_input):
    """Обработка суммы перевода"""
    # Валидация суммы
    valid, amount, error = validate_amount(amount_input)
    
    if not valid:
        vk.messages.send(
            user_id=event.user_id,
            message=f"❌ {error}",
            random_id=0
        )
        return
    
    # Получение данных
    receiver_vk_id = states.get_state_data(event.user_id, 'receiver_vk_id')
    sender = get_player_by_vk_id(session, event.user_id)
    receiver = get_player_by_vk_id(session, receiver_vk_id)
    
    # Проверка баланса
    if sender.balance < amount:
        vk.messages.send(
            user_id=event.user_id,
            message=f"❌ Недостаточно чилликов!\n💰 Ваш баланс: {sender.balance}\n💸 Требуется: {amount}",
            keyboard=get_main_menu_keyboard(),
            random_id=0
        )
        states.clear_state(event.user_id)
        return
    
    # Запрос подтверждения
    states.update_state_data(event.user_id, amount=amount)
    states.set_state(
        event.user_id,
        states.State.WAITING_TRANSFER_CONFIRM,
        receiver_vk_id=receiver_vk_id,
        amount=amount
    )
    
    confirm_msg = f"💸 Подтвердите перевод:\n\n"
    confirm_msg += f"Получатель: {receiver.first_name} {receiver.last_name}\n"
    confirm_msg += f"Сумма: {format_balance(amount)} чилликов\n"
    confirm_msg += f"Ваш баланс после перевода: {format_balance(sender.balance - amount)} чил."
    
    vk.messages.send(
        user_id=event.user_id,
        message=confirm_msg,
        keyboard=get_confirmation_keyboard(),
        random_id=0
    )


@require_not_banned
def handle_transfer_confirm(vk, event, session):
    """Подтверждение перевода"""
    # Получение данных из состояния
    receiver_vk_id = states.get_state_data(event.user_id, 'receiver_vk_id')
    amount = states.get_state_data(event.user_id, 'amount')
    
    # Выполнение перевода
    success, message = transfer_chilliki(session, vk, event.user_id, receiver_vk_id, amount)
    
    # Очистка состояния
    states.clear_state(event.user_id)
    
    # Проверка достижений
    if success:
        sender = get_player_by_vk_id(session, event.user_id)
        check_achievements(session, vk, sender)
    
    vk.messages.send(
        user_id=event.user_id,
        message=message,
        keyboard=get_main_menu_keyboard(),
        random_id=0
    )


@require_not_banned
@rate_limit
def handle_history(vk, event, session):
    """Просмотр истории транзакций"""
    states.set_state(event.user_id, states.State.WAITING_HISTORY_FILTER)
    
    vk.messages.send(
        user_id=event.user_id,
        message="📜 Выберите фильтр для истории:",
        keyboard=get_history_filter_keyboard(),
        random_id=0
    )


@require_not_banned
def handle_history_filter(vk, event, session, filter_type):
    """Обработка фильтра истории"""
    player = get_player_by_vk_id(session, event.user_id)
    
    # Маппинг фильтров
    filter_map = {
        '➡️ Переводы': 'переводы',
        'переводы': 'переводы',
        '🛒 Покупки': 'покупки',
        'покупки': 'покупки',
        '👑 Админ': 'админ',
        'админ': 'админ',
        '📋 Все': None,
        'все': None
    }
    
    transaction_filter = filter_map.get(filter_type.lower())
    
    # Получение транзакций
    transactions = get_player_transactions(session, player.id, limit=10, transaction_filter=transaction_filter)
    
    # Форматирование
    history_msg = format_transaction_history(transactions, player.id)
    
    states.clear_state(event.user_id)
    
    vk.messages.send(
        user_id=event.user_id,
        message=history_msg,
        keyboard=get_main_menu_keyboard(),
        random_id=0
    )


@require_not_banned
@rate_limit
def handle_leaderboard(vk, event, session):
    """Таблица лидеров"""
    top_players = get_top_players(session, limit=10)
    leaderboard_msg = format_leaderboard(top_players)
    
    vk.messages.send(
        user_id=event.user_id,
        message=leaderboard_msg,
        keyboard=get_main_menu_keyboard(),
        random_id=0
    )


@require_not_banned
@rate_limit
def handle_stats(vk, event, session):
    """Статистика игрока"""
    player = get_player_by_vk_id(session, event.user_id)
    transactions = get_player_transactions(session, player.id, limit=1000)
    achievements = get_player_achievements(session, player.id)
    
    # Подсчёт статистики
    total_received = sum(t.amount for t in transactions if t.to_player_id == player.id)
    total_spent = sum(t.amount for t in transactions if t.from_player_id == player.id)
    total_transfers = len([t for t in transactions if t.type.value == 'transfer' and t.from_player_id == player.id])
    total_purchases = len([t for t in transactions if t.type.value == 'purchase'])
    
    # Самая крупная покупка
    purchases = [t for t in transactions if t.type.value == 'purchase']
    largest_purchase = max(purchases, key=lambda t: t.amount) if purchases else None
    
    stats_msg = f"📊 Статистика: {player.first_name} {player.last_name}\n\n"
    stats_msg += f"💰 Текущий баланс: {format_balance(player.balance)} чил.\n"
    stats_msg += f"⭐ Уровень: {player.level}\n"
    stats_msg += f"✨ Опыт: {format_balance(player.experience)} XP\n"
    stats_msg += f"💬 Сообщений: {format_balance(player.messages_count)}\n\n"
    stats_msg += f"📈 Всего получено: {format_balance(total_received)} чил.\n"
    stats_msg += f"📉 Всего потрачено: {format_balance(total_spent)} чил.\n"
    stats_msg += f"➡️ Переводов: {total_transfers}\n"
    stats_msg += f"🛒 Покупок: {total_purchases}\n"
    
    if largest_purchase:
        stats_msg += f"💎 Крупнейшая покупка: {format_balance(largest_purchase.amount)} чил.\n"
    
    stats_msg += f"\n🏆 Достижений: {len(achievements)}"
    
    vk.messages.send(
        user_id=event.user_id,
        message=stats_msg,
        keyboard=get_main_menu_keyboard(),
        random_id=0
    )


@require_not_banned
@rate_limit
def handle_settings(vk, event, session):
    """Настройки"""
    player = get_player_by_vk_id(session, event.user_id)
    
    settings_msg = "⚙️ Настройки\n\n"
    settings_msg += f"🔔 Уведомления: {'Включены' if player.notifications_enabled else 'Выключены'}\n"
    settings_msg += f"👁️ Баланс в топе: {'Скрыт' if player.hide_balance else 'Виден'}"
    
    vk.messages.send(
        user_id=event.user_id,
        message=settings_msg,
        keyboard=get_settings_keyboard(player.notifications_enabled),
        random_id=0
    )


@require_not_banned
def handle_toggle_notifications(vk, event, session):
    """Переключение уведомлений"""
    player = get_player_by_vk_id(session, event.user_id)
    player.notifications_enabled = not player.notifications_enabled
    session.commit()
    
    status = "включены" if player.notifications_enabled else "выключены"
    vk.messages.send(
        user_id=event.user_id,
        message=f"✅ Уведомления {status}",
        keyboard=get_settings_keyboard(player.notifications_enabled),
        random_id=0
    )


@require_not_banned
def handle_toggle_hide_balance(vk, event, session):
    """Переключение скрытия баланса"""
    player = get_player_by_vk_id(session, event.user_id)
    player.hide_balance = not player.hide_balance
    session.commit()
    
    status = "скрыт" if player.hide_balance else "виден"
    vk.messages.send(
        user_id=event.user_id,
        message=f"✅ Ваш баланс теперь {status} в таблице лидеров",
        keyboard=get_settings_keyboard(player.notifications_enabled),
        random_id=0
    )