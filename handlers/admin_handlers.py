"""
Обработчики команд администратора
"""
from database.queries import (
    get_player_by_vk_id,
    get_global_stats,
    get_top_players,
    ban_player,
    unban_player,
    delete_player,
    create_scheduled_payment
)
from database.connection import get_session
from keyboards.vk_keyboards import (
    get_admin_menu_keyboard,
    get_admin_management_keyboard,
    get_confirmation_keyboard
)
from services.transaction_service import admin_give_chilliki, admin_take_chilliki
from utils.validators import validate_amount, validate_vk_id, validate_datetime_format
from utils.formatters import format_stats, format_leaderboard, format_balance
from utils.notifications import notify_ban, notify_unban
from middleware.auth import require_admin
from middleware.rate_limiter import rate_limit
import states


@require_admin
@rate_limit
def handle_admin_give_start(vk, event, session):
    """Начало процесса начисления"""
    states.set_state(event.user_id, states.State.WAITING_ADMIN_PLAYER, operation='give')
    
    vk.messages.send(
        user_id=event.user_id,
        message="💸 Начисление чилликов\n\nУкажите VK ID игрока:",
        random_id=0
    )


@require_admin
def handle_admin_give_player(vk, event, session, player_input):
    """Обработка VK ID для начисления"""
    valid, player_vk_id, error = validate_vk_id(player_input)
    
    if not valid:
        vk.messages.send(
            user_id=event.user_id,
            message=f"❌ {error}",
            random_id=0
        )
        return
    
    player = get_player_by_vk_id(session, player_vk_id)
    if not player:
        vk.messages.send(
            user_id=event.user_id,
            message=f"❌ Игрок с ID {player_vk_id} не найден",
            random_id=0
        )
        return
    
    states.update_state_data(event.user_id, player_vk_id=player_vk_id)
    states.set_state(
        event.user_id,
        states.State.WAITING_ADMIN_AMOUNT,
        operation='give',
        player_vk_id=player_vk_id
    )
    
    vk.messages.send(
        user_id=event.user_id,
        message=f"✅ Игрок: {player.first_name} {player.last_name}\n\nУкажите сумму для начисления:",
        random_id=0
    )


@require_admin
def handle_admin_give_amount(vk, event, session, amount_input):
    """Обработка суммы начисления"""
    valid, amount, error = validate_amount(amount_input)
    
    if not valid:
        vk.messages.send(
            user_id=event.user_id,
            message=f"❌ {error}",
            random_id=0
        )
        return
    
    states.update_state_data(event.user_id, amount=amount)
    states.set_state(
        event.user_id,
        states.State.WAITING_ADMIN_REASON,
        operation='give',
        player_vk_id=states.get_state_data(event.user_id, 'player_vk_id'),
        amount=amount
    )
    
    vk.messages.send(
        user_id=event.user_id,
        message=f"💰 Сумма: {format_balance(amount)} чил.\n\nУкажите причину (или отправьте '-' для пропуска):",
        random_id=0
    )


@require_admin
def handle_admin_give_reason(vk, event, session, reason_input):
    """Обработка причины и выполнение начисления"""
    player_vk_id = states.get_state_data(event.user_id, 'player_vk_id')
    amount = states.get_state_data(event.user_id, 'amount')
    reason = None if reason_input == '-' else reason_input
    
    # Выполнение начисления
    success, message = admin_give_chilliki(session, vk, event.user_id, player_vk_id, amount, reason)
    
    states.clear_state(event.user_id)
    
    vk.messages.send(
        user_id=event.user_id,
        message=message,
        keyboard=get_admin_menu_keyboard(),
        random_id=0
    )


@require_admin
@rate_limit
def handle_admin_take_start(vk, event, session):
    """Начало процесса списания"""
    states.set_state(event.user_id, states.State.WAITING_ADMIN_PLAYER, operation='take')
    
    vk.messages.send(
        user_id=event.user_id,
        message="💳 Списание чилликов\n\nУкажите VK ID игрока:",
        random_id=0
    )


@require_admin
def handle_admin_take_player(vk, event, session, player_input):
    """Обработка VK ID для списания"""
    valid, player_vk_id, error = validate_vk_id(player_input)
    
    if not valid:
        vk.messages.send(
            user_id=event.user_id,
            message=f"❌ {error}",
            random_id=0
        )
        return
    
    player = get_player_by_vk_id(session, player_vk_id)
    if not player:
        vk.messages.send(
            user_id=event.user_id,
            message=f"❌ Игрок с ID {player_vk_id} не найден",
            random_id=0
        )
        return
    
    states.update_state_data(event.user_id, player_vk_id=player_vk_id)
    states.set_state(
        event.user_id,
        states.State.WAITING_ADMIN_AMOUNT,
        operation='take',
        player_vk_id=player_vk_id
    )
    
    vk.messages.send(
        user_id=event.user_id,
        message=f"✅ Игрок: {player.first_name} {player.last_name}\n💰 Баланс: {player.balance} чил.\n\nУкажите сумму для списания:",
        random_id=0
    )


@require_admin
def handle_admin_take_amount(vk, event, session, amount_input):
    """Обработка суммы списания"""
    valid, amount, error = validate_amount(amount_input)
    
    if not valid:
        vk.messages.send(
            user_id=event.user_id,
            message=f"❌ {error}",
            random_id=0
        )
        return
    
    states.update_state_data(event.user_id, amount=amount)
    states.set_state(
        event.user_id,
        states.State.WAITING_ADMIN_REASON,
        operation='take',
        player_vk_id=states.get_state_data(event.user_id, 'player_vk_id'),
        amount=amount
    )
    
    vk.messages.send(
        user_id=event.user_id,
        message=f"💳 Сумма: {format_balance(amount)} чил.\n\nУкажите причину (или отправьте '-' для пропуска):",
        random_id=0
    )


@require_admin
def handle_admin_take_reason(vk, event, session, reason_input):
    """Обработка причины и выполнение списания"""
    player_vk_id = states.get_state_data(event.user_id, 'player_vk_id')
    amount = states.get_state_data(event.user_id, 'amount')
    reason = None if reason_input == '-' else reason_input
    
    # Выполнение списания
    success, message = admin_take_chilliki(session, vk, event.user_id, player_vk_id, amount, reason)
    
    states.clear_state(event.user_id)
    
    vk.messages.send(
        user_id=event.user_id,
        message=message,
        keyboard=get_admin_menu_keyboard(),
        random_id=0
    )


@require_admin
@rate_limit
def handle_admin_stats(vk, event, session):
    """Глобальная статистика"""
    stats = get_global_stats(session)
    top_players = get_top_players(session, limit=5, include_hidden=True)
    
    stats_msg = "📊 Глобальная статистика\n\n"
    stats_msg += f"👥 Всего игроков: {format_balance(stats['total_players'])}\n"
    stats_msg += f"💰 Общая эмиссия: {format_balance(stats['total_emission'])} чил.\n"
    stats_msg += f"📊 Средний баланс: {format_balance(int(stats['avg_balance']))} чил.\n"
    stats_msg += f"📈 Всего транзакций: {format_balance(stats['total_transactions'])}\n\n"
    stats_msg += "🏆 Топ-5 игроков:\n"
    
    for i, player in enumerate(top_players, 1):
        stats_msg += f"{i}. {player.first_name} {player.last_name} — {format_balance(player.balance)} чил.\n"
    
    vk.messages.send(
        user_id=event.user_id,
        message=stats_msg,
        keyboard=get_admin_menu_keyboard(),
        random_id=0
    )


@require_admin
@rate_limit
def handle_admin_management(vk, event, session):
    """Меню управления"""
    vk.messages.send(
        user_id=event.user_id,
        message="🔨 Управление игроками\n\nВыберите действие:",
        keyboard=get_admin_management_keyboard(),
        random_id=0
    )


@require_admin
def handle_ban_start(vk, event, session):
    """Начало блокировки игрока"""
    states.set_state(event.user_id, states.State.WAITING_BAN_PLAYER)
    
    vk.messages.send(
        user_id=event.user_id,
        message="🚫 Блокировка игрока\n\nУкажите VK ID игрока:",
        random_id=0
    )


@require_admin
def handle_ban_player(vk, event, session, player_input):
    """Обработка VK ID для блокировки"""
    valid, player_vk_id, error = validate_vk_id(player_input)
    
    if not valid:
        vk.messages.send(
            user_id=event.user_id,
            message=f"❌ {error}",
            random_id=0
        )
        return
    
    player = get_player_by_vk_id(session, player_vk_id)
    if not player:
        vk.messages.send(
            user_id=event.user_id,
            message=f"❌ Игрок с ID {player_vk_id} не найден",
            random_id=0
        )
        return
    
    states.update_state_data(event.user_id, player_vk_id=player_vk_id)
    states.set_state(event.user_id, states.State.WAITING_BAN_REASON, player_vk_id=player_vk_id)
    
    vk.messages.send(
        user_id=event.user_id,
        message=f"✅ Игрок: {player.first_name} {player.last_name}\n\nУкажите причину блокировки (или '-' для пропуска):",
        random_id=0
    )


@require_admin
def handle_ban_reason(vk, event, session, reason_input):
    """Обработка причины и блокировка"""
    player_vk_id = states.get_state_data(event.user_id, 'player_vk_id')
    reason = None if reason_input == '-' else reason_input
    
    success = ban_player(session, player_vk_id, reason)
    
    if success:
        notify_ban(vk, player_vk_id, reason)
        vk.messages.send(
            user_id=event.user_id,
            message=f"✅ Игрок заблокирован",
            keyboard=get_admin_management_keyboard(),
            random_id=0
        )
    else:
        vk.messages.send(
            user_id=event.user_id,
            message=f"❌ Ошибка блокировки",
            keyboard=get_admin_management_keyboard(),
            random_id=0
        )
    
    states.clear_state(event.user_id)


@require_admin
def handle_delete_player_start(vk, event, session):
    """Начало удаления игрока"""
    states.set_state(event.user_id, states.State.WAITING_DELETE_PLAYER)
    
    vk.messages.send(
        user_id=event.user_id,
        message="🗑️ Удаление профиля\n\n⚠️ ВНИМАНИЕ: Это действие необратимо!\n\nУкажите VK ID игрока:",
        random_id=0
    )


@require_admin
def handle_delete_player_confirm(vk, event, session, player_input):
    """Подтверждение и удаление игрока"""
    valid, player_vk_id, error = validate_vk_id(player_input)
    
    if not valid:
        vk.messages.send(
            user_id=event.user_id,
            message=f"❌ {error}",
            random_id=0
        )
        return
    
    player = get_player_by_vk_id(session, player_vk_id)
    if not player:
        vk.messages.send(
            user_id=event.user_id,
            message=f"❌ Игрок с ID {player_vk_id} не найден",
            random_id=0
        )
        states.clear_state(event.user_id)
        return
    
    success = delete_player(session, player_vk_id)
    
    if success:
        vk.messages.send(
            user_id=event.user_id,
            message=f"✅ Профиль игрока {player.first_name} {player.last_name} удалён",
            keyboard=get_admin_management_keyboard(),
            random_id=0
        )
    else:
        vk.messages.send(
            user_id=event.user_id,
            message=f"❌ Ошибка удаления",
            keyboard=get_admin_management_keyboard(),
            random_id=0
        )
    
    states.clear_state(event.user_id)
    """
Дополнительные команды администратора
"""
from sqlalchemy import func
from database.models import Player
from database.queries import create_scheduled_payment
from utils.validators import validate_datetime_format
from datetime import datetime


@require_admin
def handle_schedule_start(vk, event, session):
    """Начало запланированного начисления"""
    states.set_state(event.user_id, states.State.WAITING_SCHEDULE_PLAYER)
    
    vk.messages.send(
        user_id=event.user_id,
        message="⏰ Запланировать начисление\n\nУкажите VK ID игрока:",
        random_id=0
    )


@require_admin
def handle_schedule_player(vk, event, session, player_input):
    """Обработка VK ID для планировщика"""
    valid, player_vk_id, error = validate_vk_id(player_input)
    
    if not valid:
        vk.messages.send(
            user_id=event.user_id,
            message=f"❌ {error}",
            random_id=0
        )
        return
    
    player = get_player_by_vk_id(session, player_vk_id)
    if not player:
        vk.messages.send(
            user_id=event.user_id,
            message=f"❌ Игрок с ID {player_vk_id} не найден",
            random_id=0
        )
        return
    
    states.update_state_data(event.user_id, player_vk_id=player_vk_id)
    states.set_state(
        event.user_id,
        states.State.WAITING_SCHEDULE_AMOUNT,
        player_vk_id=player_vk_id
    )
    
    vk.messages.send(
        user_id=event.user_id,
        message=f"✅ Игрок: {player.first_name} {player.last_name}\n\nУкажите сумму:",
        random_id=0
    )


@require_admin
def handle_schedule_amount(vk, event, session, amount_input):
    """Обработка суммы для планировщика"""
    valid, amount, error = validate_amount(amount_input)
    
    if not valid:
        vk.messages.send(
            user_id=event.user_id,
            message=f"❌ {error}",
            random_id=0
        )
        return
    
    states.update_state_data(event.user_id, amount=amount)
    states.set_state(
        event.user_id,
        states.State.WAITING_SCHEDULE_DATETIME,
        player_vk_id=states.get_state_data(event.user_id, 'player_vk_id'),
        amount=amount
    )
    
    vk.messages.send(
        user_id=event.user_id,
        message=f"💰 Сумма: {format_balance(amount)} чил.\n\nУкажите дату и время (ГГГГ-ММ-ДД ЧЧ:ММ):",
        random_id=0
    )


@require_admin
def handle_schedule_datetime(vk, event, session, datetime_input):
    """Обработка даты/времени для планировщика"""
    valid, scheduled_dt, error = validate_datetime_format(datetime_input)
    
    if not valid:
        vk.messages.send(
            user_id=event.user_id,
            message=f"❌ {error}",
            random_id=0
        )
        return
    
    if scheduled_dt < datetime.now():
        vk.messages.send(
            user_id=event.user_id,
            message="❌ Дата должна быть в будущем!",
            random_id=0
        )
        return
    
    states.update_state_data(event.user_id, scheduled_dt=scheduled_dt)
    states.set_state(
        event.user_id,
        states.State.WAITING_SCHEDULE_REASON,
        player_vk_id=states.get_state_data(event.user_id, 'player_vk_id'),
        amount=states.get_state_data(event.user_id, 'amount'),
        scheduled_dt=scheduled_dt
    )
    
    vk.messages.send(
        user_id=event.user_id,
        message=f"⏰ Дата: {scheduled_dt.strftime('%d.%m.%Y %H:%M')}\n\nУкажите причину (или '-' для пропуска):",
        random_id=0
    )


@require_admin
def handle_schedule_reason(vk, event, session, reason_input):
    """Создание запланированного начисления"""
    player_vk_id = states.get_state_data(event.user_id, 'player_vk_id')
    amount = states.get_state_data(event.user_id, 'amount')
    scheduled_dt = states.get_state_data(event.user_id, 'scheduled_dt')
    reason = None if reason_input == '-' else reason_input
    
    player = get_player_by_vk_id(session, player_vk_id)
    
    payment = create_scheduled_payment(
        session,
        player.id,
        event.user_id,
        amount,
        scheduled_dt,
        reason
    )
    
    if payment:
        msg = f"✅ Запланировано начисление\n\n"
        msg += f"Игрок: {player.first_name} {player.last_name}\n"
        msg += f"Сумма: {format_balance(amount)} чил.\n"
        msg += f"Дата: {scheduled_dt.strftime('%d.%m.%Y %H:%M')}\n"
        if reason:
            msg += f"Причина: {reason}"
    else:
        msg = "❌ Ошибка создания запланированного начисления"
    
    states.clear_state(event.user_id)
    
    vk.messages.send(
        user_id=event.user_id,
        message=msg,
        keyboard=get_admin_menu_keyboard(),
        random_id=0
    )


@require_admin
def handle_broadcast_start(vk, event, session):
    """Начало рассылки"""
    states.set_state(event.user_id, states.State.WAITING_BROADCAST_MESSAGE)
    
    vk.messages.send(
        user_id=event.user_id,
        message="📢 Рассылка сообщения всем игрокам\n\nВведите текст сообщения:",
        random_id=0
    )


@require_admin
def handle_broadcast_send(vk, event, session, message_text):
    """Отправка рассылки"""
    # Получение всех игроков
    players = session.query(Player).filter_by(is_banned=False).all()
    
    sent_count = 0
    failed_count = 0
    
    broadcast_msg = f"📢 Сообщение от администратора:\n\n{message_text}"
    
    for player in players:
        try:
            vk.messages.send(
                user_id=player.vk_id,
                message=broadcast_msg,
                random_id=0
            )
            sent_count += 1
        except Exception as e:
            failed_count += 1
            print(f"❌ Ошибка отправки {player.vk_id}: {e}")
    
    states.clear_state(event.user_id)
    
    result_msg = f"✅ Рассылка завершена\n\n"
    result_msg += f"Отправлено: {sent_count}\n"
    result_msg += f"Ошибок: {failed_count}"
    
    vk.messages.send(
        user_id=event.user_id,
        message=result_msg,
        keyboard=get_admin_menu_keyboard(),
        random_id=0
    )


@require_admin
def handle_gift_all_start(vk, event, session):
    """Начало массового начисления"""
    states.set_state(event.user_id, states.State.WAITING_GIFT_ALL_AMOUNT)
    
    vk.messages.send(
        user_id=event.user_id,
        message="🎁 Начислить чиллики всем игрокам\n\nУкажите сумму:",
        random_id=0
    )


@require_admin
def handle_gift_all_amount(vk, event, session, amount_input):
    """Массовое начисление всем игрокам"""
    valid, amount, error = validate_amount(amount_input)
    
    if not valid:
        vk.messages.send(
            user_id=event.user_id,
            message=f"❌ {error}",
            random_id=0
        )
        return
    
    # Получение всех игроков
    players = session.query(Player).all()
    
    for player in players:
        player.balance += amount
        
        # Создание транзакции
        create_transaction(
            session,
            from_player_id=None,
            to_player_id=player.id,
            amount=amount,
            transaction_type=TransactionType.ADMIN_GIVE,
            reason=f"Массовое начисление от администратора"
        )
    
    session.commit()
    
    # Уведомление игроков
    for player in players:
        if player.notifications_enabled:
            try:
                vk.messages.send(
                    user_id=player.vk_id,
                    message=f"🎁 Вам начислено {format_balance(amount)} чилликов!\n💰 Ваш баланс: {format_balance(player.balance)} чил.",
                    random_id=0
                )
            except:
                pass
    
    states.clear_state(event.user_id)
    
    vk.messages.send(
        user_id=event.user_id,
        message=f"✅ Начислено {format_balance(amount)} чилликов всем игрокам ({len(players)} чел.)",
        keyboard=get_admin_menu_keyboard(),
        random_id=0
    )


@require_admin
def handle_find_player_start(vk, event, session):
    """Поиск игрока"""
    states.set_state(event.user_id, states.State.WAITING_FIND_PLAYER)
    
    vk.messages.send(
        user_id=event.user_id,
        message="🔍 Поиск игрока\n\nВведите имя или VK ID:",
        random_id=0
    )


@require_admin
def handle_find_player_search(vk, event, session, search_query):
    """Обработка поиска"""
    # Попытка поиска по VK ID
    valid, vk_id, _ = validate_vk_id(search_query)
    
    if valid:
        player = get_player_by_vk_id(session, vk_id)
        if player:
            msg = format_player_profile(player, include_achievements=False)
            vk.messages.send(
                user_id=event.user_id,
                message=msg,
                keyboard=get_admin_management_keyboard(),
                random_id=0
            )
            states.clear_state(event.user_id)
            return
    
    # Поиск по имени
    players = session.query(Player).filter(
        func.lower(Player.first_name + ' ' + Player.last_name).like(f'%{search_query.lower()}%')
    ).limit(10).all()
    
    if not players:
        vk.messages.send(
            user_id=event.user_id,
            message="❌ Игроки не найдены",
            keyboard=get_admin_management_keyboard(),
            random_id=0
        )
    else:
        msg = f"🔍 Найдено игроков: {len(players)}\n\n"
        for player in players:
            msg += f"• {player.first_name} {player.last_name}\n"
            msg += f"  VK ID: {player.vk_id}\n"
            msg += f"  Баланс: {format_balance(player.balance)} чил.\n\n"
        
        vk.messages.send(
            user_id=event.user_id,
            message=msg,
            keyboard=get_admin_management_keyboard(),
            random_id=0
        )
    
    states.clear_state(event.user_id)