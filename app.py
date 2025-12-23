"""
Главный файл Chill Bot
Точка входа приложения
"""
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id

import config
from database.connection import init_db, get_session, close_session
from database.queries import get_or_create_player
from services.scheduler_service import SchedulerService
import states

# Импорт обработчиков
from handlers import common_handlers, player_handlers, admin_handlers, request_handlers
from middleware.auth import is_admin


def init_vk():
    """Инициализация VK API"""
    vk_session = vk_api.VkApi(token=config.VK_GROUP_TOKEN)
    vk = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)
    
    print("✅ VK API инициализирован")
    return vk, longpoll


def route_message(vk, event, session):
    """Маршрутизация сообщений к соответствующим обработчикам"""
    text = event.text.strip()
    text_lower = text.lower()
    user_id = event.user_id
    
    # Получение текущего состояния пользователя
    current_state, state_data = states.get_state(user_id)
    
    # === ОБРАБОТКА СОСТОЯНИЙ (FSM) ===
    
    # Отмена операции
    if text_lower in ['❌ отменить', 'отменить', 'отмена', 'cancel']:
        common_handlers.handle_cancel(vk, event, session)
        return
    
    # Обработка состояний переводов
    if current_state == states.State.WAITING_RECEIVER:
        player_handlers.handle_transfer_receiver(vk, event, session, text)
        return
    
    if current_state == states.State.WAITING_TRANSFER_AMOUNT:
        player_handlers.handle_transfer_amount(vk, event, session, text)
        return
    
    if current_state == states.State.WAITING_TRANSFER_CONFIRM:
        if text_lower in ['✅ подтвердить', 'да', 'подтвердить']:
            player_handlers.handle_transfer_confirm(vk, event, session)
        else:
            common_handlers.handle_cancel(vk, event, session)
        return
    
    # Обработка состояний покупок
    if current_state == states.State.WAITING_PURCHASE_CATEGORY:
        request_handlers.handle_purchase_category(vk, event, session, text)
        return
    
    if current_state == states.State.WAITING_PURCHASE_REQUEST:
        request_handlers.handle_purchase_request(vk, event, session, text)
        return
    
    if current_state == states.State.WAITING_PURCHASE_CONFIRM:
        if text_lower in ['✅ подтвердить', 'да', 'подтвердить']:
            request_handlers.handle_purchase_confirm(vk, event, session)
        else:
            common_handlers.handle_cancel(vk, event, session)
        return
    
    # Обработка фильтра истории
    if current_state == states.State.WAITING_HISTORY_FILTER:
        player_handlers.handle_history_filter(vk, event, session, text)
        return
    
    # === ОБРАБОТКА АДМИНСКИХ СОСТОЯНИЙ ===
    
    # Начисление/списание
    if current_state == states.State.WAITING_ADMIN_PLAYER:
        operation = state_data.get('operation')
        if operation == 'give':
            admin_handlers.handle_admin_give_player(vk, event, session, text)
        elif operation == 'take':
            admin_handlers.handle_admin_take_player(vk, event, session, text)
        return
    
    if current_state == states.State.WAITING_ADMIN_AMOUNT:
        operation = state_data.get('operation')
        if operation == 'give':
            admin_handlers.handle_admin_give_amount(vk, event, session, text)
        elif operation == 'take':
            admin_handlers.handle_admin_take_amount(vk, event, session, text)
        return
    
    if current_state == states.State.WAITING_ADMIN_REASON:
        operation = state_data.get('operation')
        if operation == 'give':
            admin_handlers.handle_admin_give_reason(vk, event, session, text)
        elif operation == 'take':
            admin_handlers.handle_admin_take_reason(vk, event, session, text)
        return
    
    # Запланированные начисления
    if current_state == states.State.WAITING_SCHEDULE_PLAYER:
        admin_handlers.handle_schedule_player(vk, event, session, text)
        return
    
    if current_state == states.State.WAITING_SCHEDULE_AMOUNT:
        admin_handlers.handle_schedule_amount(vk, event, session, text)
        return
    
    if current_state == states.State.WAITING_SCHEDULE_DATETIME:
        admin_handlers.handle_schedule_datetime(vk, event, session, text)
        return
    
    if current_state == states.State.WAITING_SCHEDULE_REASON:
        admin_handlers.handle_schedule_reason(vk, event, session, text)
        return
    
    # Управление игроками
    if current_state == states.State.WAITING_BAN_PLAYER:
        admin_handlers.handle_ban_player(vk, event, session, text)
        return
    
    if current_state == states.State.WAITING_BAN_REASON:
        admin_handlers.handle_ban_reason(vk, event, session, text)
        return
    
    if current_state == states.State.WAITING_DELETE_PLAYER:
        admin_handlers.handle_delete_player_confirm(vk, event, session, text)
        return
    
    if current_state == states.State.WAITING_FIND_PLAYER:
        admin_handlers.handle_find_player_search(vk, event, session, text)
        return
    
    # Рассылка
    if current_state == states.State.WAITING_BROADCAST_MESSAGE:
        admin_handlers.handle_broadcast_send(vk, event, session, text)
        return
    
    if current_state == states.State.WAITING_GIFT_ALL_AMOUNT:
        admin_handlers.handle_gift_all_amount(vk, event, session, text)
        return
    
    # === ОБРАБОТКА КОМАНД (БЕЗ СОСТОЯНИЯ) ===
    
    # Общие команды
    if text_lower in ['начать', '/start', 'start']:
        common_handlers.handle_start(vk, event, session)
        return
    
    if text_lower in ['помощь', '/help', 'help', '❓ помощь']:
        common_handlers.handle_help(vk, event, session)
        return
    
    # Команды игрока
    if text_lower in ['баланс', '/balance', '💰 баланс']:
        player_handlers.handle_balance(vk, event, session)
        return
    
    if text_lower in ['перевести', '/transfer', '➡️ перевести']:
        player_handlers.handle_transfer_start(vk, event, session)
        return
    
    if text_lower in ['история', '/history', '📜 история']:
        player_handlers.handle_history(vk, event, session)
        return
    
    if text_lower in ['топ', 'лидеры', '/leaderboard', '🏆 топ игроков']:
        player_handlers.handle_leaderboard(vk, event, session)
        return
    
    if text_lower in ['статистика', '/stats', '📊 статистика']:
        player_handlers.handle_stats(vk, event, session)
        return
    
    if text_lower in ['настройки', '/settings', '⚙️ настройки']:
        player_handlers.handle_settings(vk, event, session)
        return
    
    if text_lower in ['купить', '/buy', '🛒 купить']:
        request_handlers.handle_purchase_start(vk, event, session)
        return
    
    # Настройки
    if text_lower in ['🔔 выключить уведомления', '🔕 включить уведомления']:
        player_handlers.handle_toggle_notifications(vk, event, session)
        return
    
    if text_lower in ['👁️ скрыть баланс в топе', '👁️‍🗨️ показать баланс в топе']:
        player_handlers.handle_toggle_hide_balance(vk, event, session)
        return
    
    # Админские команды
    if is_admin(user_id):
        if text_lower in ['начислить', '/give', '💸 начислить']:
            admin_handlers.handle_admin_give_start(vk, event, session)
            return
        
        if text_lower in ['списать', '/take', '💳 списать']:
            admin_handlers.handle_admin_take_start(vk, event, session)
            return
        
        if text_lower in ['админ статистика', '/admin_stats', '📊 статистика'] and is_admin(user_id):
            admin_handlers.handle_admin_stats(vk, event, session)
            return
        
        if text_lower in ['управление', '/management', '🔨 управление']:
            admin_handlers.handle_admin_management(vk, event, session)
            return
        
        if text_lower in ['забанить', '/ban', '🚫 забанить']:
            admin_handlers.handle_ban_start(vk, event, session)
            return
        
        if text_lower in ['удалить', '/delete', '🗑️ удалить профиль']:
            admin_handlers.handle_delete_player_start(vk, event, session)
            return
        
        if text_lower in ['запланировать', '/schedule', '⏰ запланировать']:
            admin_handlers.handle_schedule_start(vk, event, session)
            return
        
        if text_lower in ['рассылка', '/broadcast', '📢 рассылка']:
            admin_handlers.handle_broadcast_start(vk, event, session)
            return
        
        if text_lower in ['начислить всем', '/gift_all', '🎁 начислить всем']:
            admin_handlers.handle_gift_all_start(vk, event, session)
            return
        
        if text_lower in ['найти', '/find', '🔍 найти игрока']:
            admin_handlers.handle_find_player_start(vk, event, session)
            return
        
        # Обработка ответа админа на запрос покупки
        if 'стоимость:' in text_lower or 'цена:' in text_lower or 'отклонено:' in text_lower:
            request_handlers.handle_admin_price_response(vk, event, session, text)
            return
    
    # Если команда не распознана
    vk.messages.send(
        user_id=user_id,
        message="❓ Команда не распознана. Используйте /help для справки",
        random_id=0
    )


def main():
    """Главная функция бота"""
    print("=" * 50)
    print("🎮 CHILL BOT - ЗАПУСК")
    print("=" * 50)
    
    # Инициализация БД
    print("\n📦 Инициализация базы данных...")
    init_db()
    
    # Инициализация VK API
    print("\n🔌 Подключение к VK API...")
    vk, longpoll = init_vk()
    
    # Запуск планировщика
    print("\n⏰ Запуск планировщика...")
    scheduler = SchedulerService(vk)
    scheduler.start()
    
    print("\n" + "=" * 50)
    print("✅ БОТ ЗАПУЩЕН И ГОТОВ К РАБОТЕ!")
    print("=" * 50)
    print("\nОжидание событий...\n")
    
    try:
        # Основной цикл обработки событий
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                session = get_session()
                
                try:
                    # Получение информации о пользователе
                    user_info = vk.users.get(user_ids=event.user_id)[0]
                    first_name = user_info['first_name']
                    last_name = user_info['last_name']
                    
                    # Автоматическое создание/обновление профиля
                    player = get_or_create_player(session, event.user_id, first_name, last_name)
                    
                    # Трекинг сообщений для опыта (кроме команд)
                    if not event.text.startswith('/') and not event.text.startswith('❌'):
                        common_handlers.track_message(vk, event, session)
                    
                    # Маршрутизация сообщения
                    route_message(vk, event, session)
                    
                except Exception as e:
                    print(f"❌ Ошибка обработки сообщения от {event.user_id}: {e}")
                    vk.messages.send(
                        user_id=event.user_id,
                        message="❌ Произошла ошибка. Попробуйте позже.",
                        random_id=0
                    )
                
                finally:
                    close_session(session)
    
    except KeyboardInterrupt:
        print("\n\n⏸️ Остановка бота...")
        scheduler.stop()
        print("✅ Бот остановлен")
    
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        scheduler.stop()


if __name__ == "__main__":
    main()