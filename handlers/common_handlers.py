"""
Общие обработчики команд (для всех пользователей)
"""
from database.queries import get_or_create_player, increment_message_count
from keyboards.vk_keyboards import get_main_menu_keyboard, get_admin_menu_keyboard
from middleware.auth import is_admin
from utils.formatters import format_level_up
from utils.notifications import send_notification
import states


def handle_start(vk, event, session):
    """Обработка команды /start или 'начать'"""
    # Получение информации о пользователе
    user_info = vk.users.get(user_ids=event.user_id)[0]
    first_name = user_info['first_name']
    last_name = user_info['last_name']
    
    # Создание/получение профиля
    player = get_or_create_player(session, event.user_id, first_name, last_name)
    
    # Приветствие
    if is_admin(event.user_id):
        welcome_msg = f"👋 Привет, {first_name}!\n\n"
        welcome_msg += "🎮 Вы вошли в бот проекта Chill\n"
        welcome_msg += "👑 У вас есть права администратора\n\n"
        welcome_msg += f"💰 Ваш баланс: {player.balance} чилликов\n"
        welcome_msg += f"⭐ Уровень: {player.level}\n\n"
        welcome_msg += "Выберите режим работы:"
        
        vk.messages.send(
            user_id=event.user_id,
            message=welcome_msg,
            keyboard=get_admin_menu_keyboard(),
            random_id=0
        )
    else:
        welcome_msg = f"👋 Привет, {first_name}!\n\n"
        welcome_msg += "🎮 Добро пожаловать в бот проекта Chill!\n\n"
        welcome_msg += f"💰 Ваш баланс: {player.balance} чилликов\n"
        welcome_msg += f"⭐ Уровень: {player.level}\n\n"
        welcome_msg += "Используйте кнопки ниже для взаимодействия:"
        
        vk.messages.send(
            user_id=event.user_id,
            message=welcome_msg,
            keyboard=get_main_menu_keyboard(),
            random_id=0
        )


def handle_help(vk, event, session):
    """Обработка команды /help или '❓ Помощь'"""
    if is_admin(event.user_id):
        help_msg = "📖 Справка по командам бота\n\n"
        help_msg += "👤 ИГРОК:\n"
        help_msg += "💰 Баланс — просмотр вашего баланса\n"
        help_msg += "➡️ Перевести — перевод чилликов игроку\n"
        help_msg += "🛒 Купить — запрос на покупку способности\n"
        help_msg += "📜 История — история транзакций\n"
        help_msg += "🏆 Топ игроков — таблица лидеров\n"
        help_msg += "📊 Статистика — ваша статистика\n"
        help_msg += "⚙️ Настройки — настройки уведомлений\n\n"
        help_msg += "👑 АДМИНИСТРАТОР:\n"
        help_msg += "💸 Начислить — начислить чиллики игроку\n"
        help_msg += "💳 Списать — списать чиллики у игрока\n"
        help_msg += "🔨 Управление — бан/разбан/удаление\n"
        help_msg += "📢 Рассылка — отправить сообщение всем\n"
        help_msg += "⏰ Запланировать — запланировать начисление\n"
        help_msg += "🎁 Начислить всем — массовое начисление\n"
    else:
        help_msg = "📖 Справка по командам бота\n\n"
        help_msg += "💰 Баланс — просмотр вашего баланса и профиля\n"
        help_msg += "➡️ Перевести — перевод чилликов другому игроку\n"
        help_msg += "🛒 Купить — запрос на покупку способности/предмета\n"
        help_msg += "📜 История — просмотр истории транзакций\n"
        help_msg += "🏆 Топ игроков — таблица лидеров\n"
        help_msg += "📊 Статистика — ваша статистика и достижения\n"
        help_msg += "⚙️ Настройки — управление уведомлениями\n\n"
        help_msg += "💡 Чиллики — внутренняя валюта проекта\n"
        help_msg += "Зарабатывайте их и покупайте способности!\n\n"
        help_msg += "❓ Вопросы? Обратитесь к администратору."
    
    vk.messages.send(
        user_id=event.user_id,
        message=help_msg,
        random_id=0
    )


def handle_cancel(vk, event, session):
    """Отмена текущей операции"""
    current_state, _ = states.get_state(event.user_id)
    
    if current_state == states.State.IDLE:
        vk.messages.send(
            user_id=event.user_id,
            message="❌ Нет активных операций для отмены",
            keyboard=get_main_menu_keyboard() if not is_admin(event.user_id) else get_admin_menu_keyboard(),
            random_id=0
        )
    else:
        states.clear_state(event.user_id)
        vk.messages.send(
            user_id=event.user_id,
            message="✅ Операция отменена",
            keyboard=get_main_menu_keyboard() if not is_admin(event.user_id) else get_admin_menu_keyboard(),
            random_id=0
        )


def track_message(vk, event, session):
    """Отслеживание сообщений для начисления опыта"""
    player = get_or_create_player(
        session,
        event.user_id,
        "Игрок",  # Будет обновлено при /start
        ""
    )
    
    # Начисление опыта за сообщение
    level_up, new_level = increment_message_count(session, player.id)
    
    # Уведомление о повышении уровня
    if level_up:
        msg = format_level_up(new_level)
        send_notification(vk, event.user_id, msg)