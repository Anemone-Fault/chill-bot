"""
Обработчики запросов на покупку способностей/предметов
"""
from database.queries import create_purchase_request, get_player_by_vk_id
from database.models import PurchaseRequest
from keyboards.vk_keyboards import (
    get_category_keyboard,
    get_confirmation_keyboard,
    get_main_menu_keyboard
)
from services.transaction_service import purchase_item
from utils.validators import parse_price_from_admin
from utils.notifications import notify_purchase_approved, notify_purchase_rejected
from middleware.auth import require_not_banned, is_admin
from middleware.rate_limiter import rate_limit, hourly_limit
import states
import config


@require_not_banned
@rate_limit
@hourly_limit
def handle_purchase_start(vk, event, session):
    """Начало процесса покупки"""
    states.set_state(event.user_id, states.State.WAITING_PURCHASE_CATEGORY)
    
    vk.messages.send(
        user_id=event.user_id,
        message="🛒 Запрос на покупку\n\nВыберите категорию или напишите свой запрос:",
        keyboard=get_category_keyboard(),
        random_id=0
    )


@require_not_banned
def handle_purchase_category(vk, event, session, category):
    """Обработка выбора категории"""
    # Маппинг категорий
    category_map = {
        '🔥 Боевые': 'Боевая способность',
        '🛡️ Защитные': 'Защитная способность',
        '⚡ Утилити': 'Утилити способность',
        '🎒 Предметы': 'Предмет',
        '✏️ Свой запрос': None
    }
    
    if category in category_map:
        category_text = category_map[category]
        if category_text:
            # Пропускаем к описанию
            states.set_state(
                event.user_id,
                states.State.WAITING_PURCHASE_REQUEST,
                category=category_text
            )
            vk.messages.send(
                user_id=event.user_id,
                message=f"✅ Категория: {category_text}\n\nОпишите, что именно вы хотите:",
                random_id=0
            )
        else:
            # Свой запрос
            states.set_state(event.user_id, states.State.WAITING_PURCHASE_REQUEST)
            vk.messages.send(
                user_id=event.user_id,
                message="✏️ Опишите ваш запрос:",
                random_id=0
            )
    else:
        # Если не кнопка, а свободный текст
        handle_purchase_request(vk, event, session, category)


@require_not_banned
def handle_purchase_request(vk, event, session, description):
    """Обработка описания запроса"""
    player = get_player_by_vk_id(session, event.user_id)
    category = states.get_state_data(event.user_id, 'category')
    
    # Формирование полного описания
    if category:
        full_description = f"[{category}] {description}"
    else:
        full_description = description
    
    # Создание запроса
    purchase_request = create_purchase_request(session, player.id, full_description)
    
    # Уведомление игрока
    vk.messages.send(
        user_id=event.user_id,
        message=f"✅ Ваш запрос отправлен администратору!\n\n💬 Запрос: {full_description}\n\nОжидайте ответа...",
        keyboard=get_main_menu_keyboard(),
        random_id=0
    )
    
    # Уведомление всех администраторов
    admin_msg = f"📥 Новый запрос на покупку\n\n"
    admin_msg += f"От: {player.first_name} {player.last_name} (VK ID: {player.vk_id})\n"
    admin_msg += f"Баланс игрока: {player.balance} чил.\n\n"
    admin_msg += f"💬 Запрос: {full_description}\n\n"
    admin_msg += f"📌 ID запроса: {purchase_request.id}\n\n"
    admin_msg += f"Ответьте в формате:\nСтоимость: <число>\nили\nОтклонено: <причина>"
    
    for admin_id in config.ADMIN_IDS:
        try:
            vk.messages.send(
                user_id=admin_id,
                message=admin_msg,
                random_id=0
            )
        except Exception as e:
            print(f"❌ Ошибка отправки админу {admin_id}: {e}")
    
    states.clear_state(event.user_id)


def handle_admin_price_response(vk, event, session, text):
    """
    Обработка ответа администратора на запрос (установка цены или отклонение)
    Вызывается когда админ отвечает на сообщение с запросом
    """
    if not is_admin(event.user_id):
        return
    
    # Попытка парсинга цены
    valid_price, price, _ = parse_price_from_admin(text)
    
    # Поиск активных запросов (упрощённо - берём последний pending)
    pending_request = session.query(PurchaseRequest).filter_by(
        status='pending'
    ).order_by(PurchaseRequest.created_at.desc()).first()
    
    if not pending_request:
        vk.messages.send(
            user_id=event.user_id,
            message="❌ Нет активных запросов",
            random_id=0
        )
        return
    
    player = get_player_by_vk_id(session, pending_request.player_id)
    
    # Проверка на отклонение
    if text.lower().startswith('отклонено:') or text.lower().startswith('отклонить:'):
        reason = text.split(':', 1)[1].strip() if ':' in text else "Не указана"
        
        pending_request.status = 'rejected'
        pending_request.admin_response = reason
        session.commit()
        
        # Уведомление игрока
        notify_purchase_rejected(vk, session, player.vk_id, pending_request.item_description, reason)
        
        vk.messages.send(
            user_id=event.user_id,
            message=f"✅ Запрос отклонён\n\nИгрок: {player.first_name} {player.last_name}\nПричина: {reason}",
            random_id=0
        )
        return
    
    if not valid_price:
        vk.messages.send(
            user_id=event.user_id,
            message="❌ Не удалось распознать цену. Используйте формат: 'Стоимость: 123' или 'Отклонено: причина'",
            random_id=0
        )
        return
    
    # Установка цены
    pending_request.price = price
    pending_request.status = 'approved'
    session.commit()
    
    # Проверка баланса игрока
    if player.balance < price:
        msg = f"💰 Стоимость установлена: {price} чил.\n\n"
        msg += f"⚠️ У игрока недостаточно средств!\n"
        msg += f"Баланс: {player.balance} чил."
        
        vk.messages.send(
            user_id=event.user_id,
            message=msg,
            random_id=0
        )
        
        # Уведомление игрока о недостаточном балансе
        player_msg = f"❌ Ваш запрос одобрен, но недостаточно чилликов!\n\n"
        player_msg += f"💬 Запрос: {pending_request.item_description}\n"
        player_msg += f"💰 Стоимость: {price} чил.\n"
        player_msg += f"💳 Ваш баланс: {player.balance} чил.\n\n"
        player_msg += f"Накопите недостающую сумму!"
        
        vk.messages.send(
            user_id=player.vk_id,
            message=player_msg,
            random_id=0
        )
        return
    
    # Запрос подтверждения у игрока
    confirm_msg = f"✅ Ваш запрос одобрен!\n\n"
    confirm_msg += f"💬 Запрос: {pending_request.item_description}\n"
    confirm_msg += f"💰 Стоимость: {price} чилликов\n"
    confirm_msg += f"💳 Ваш баланс: {player.balance} чил.\n"
    confirm_msg += f"💵 Остаток после покупки: {player.balance - price} чил.\n\n"
    confirm_msg += f"Подтвердите покупку:"
    
    # Сохраняем ID запроса для подтверждения
    states.set_state(
        player.vk_id,
        states.State.WAITING_PURCHASE_CONFIRM,
        request_id=pending_request.id
    )
    
    vk.messages.send(
        user_id=player.vk_id,
        message=confirm_msg,
        keyboard=get_confirmation_keyboard(),
        random_id=0
    )
    
    # Уведомление админа
    vk.messages.send(
        user_id=event.user_id,
        message=f"✅ Цена установлена: {price} чил.\n\nИгроку отправлен запрос на подтверждение",
        random_id=0
    )


@require_not_banned
def handle_purchase_confirm(vk, event, session):
    """Подтверждение покупки игроком"""
    request_id = states.get_state_data(event.user_id, 'request_id')
    
    if not request_id:
        vk.messages.send(
            user_id=event.user_id,
            message="❌ Запрос не найден",
            keyboard=get_main_menu_keyboard(),
            random_id=0
        )
        return
    
    # Получение запроса
    purchase_request = session.query(PurchaseRequest).filter_by(id=request_id).first()
    
    if not purchase_request or purchase_request.status != 'approved':
        vk.messages.send(
            user_id=event.user_id,
            message="❌ Запрос недействителен",
            keyboard=get_main_menu_keyboard(),
            random_id=0
        )
        states.clear_state(event.user_id)
        return
    
    player = get_player_by_vk_id(session, event.user_id)
    
    # Выполнение покупки
    success, message = purchase_item(
        session,
        vk,
        player.vk_id,
        purchase_request.item_description,
        purchase_request.price
    )
    
    if success:
        purchase_request.status = 'completed'
        session.commit()
        
        # Проверка достижений
        check_achievements(session, vk, player)
        
        # Уведомление администраторов
        admin_msg = f"✅ Покупка завершена\n\n"
        admin_msg += f"Игрок: {player.first_name} {player.last_name}\n"
        admin_msg += f"Предмет: {purchase_request.item_description}\n"
        admin_msg += f"Сумма: {purchase_request.price} чил."
        
        for admin_id in config.ADMIN_IDS:
            try:
                vk.messages.send(
                    user_id=admin_id,
                    message=admin_msg,
                    random_id=0
                )
            except:
                pass
    
    states.clear_state(event.user_id)
    
    vk.messages.send(
        user_id=event.user_id,
        message=message,
        keyboard=get_main_menu_keyboard(),
        random_id=0
    )