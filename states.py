"""
FSM (Finite State Machine) для управления состояниями диалогов
"""
from collections import defaultdict
from datetime import datetime, timedelta
import config

# In-memory хранилище состояний пользователей
user_states = defaultdict(dict)

# Временные данные для подтверждений
pending_confirmations = {}


class State:
    """Константы состояний"""
    IDLE = 'idle'
    
    # Переводы
    WAITING_RECEIVER = 'waiting_receiver'
    WAITING_TRANSFER_AMOUNT = 'waiting_transfer_amount'
    WAITING_TRANSFER_CONFIRM = 'waiting_transfer_confirm'
    
    # Покупки
    WAITING_PURCHASE_REQUEST = 'waiting_purchase_request'
    WAITING_PURCHASE_CATEGORY = 'waiting_purchase_category'
    WAITING_PURCHASE_CONFIRM = 'waiting_purchase_confirm'
    
    # Админские операции
    WAITING_ADMIN_PLAYER = 'waiting_admin_player'
    WAITING_ADMIN_AMOUNT = 'waiting_admin_amount'
    WAITING_ADMIN_REASON = 'waiting_admin_reason'
    
    # Запланированные начисления
    WAITING_SCHEDULE_PLAYER = 'waiting_schedule_player'
    WAITING_SCHEDULE_AMOUNT = 'waiting_schedule_amount'
    WAITING_SCHEDULE_DATETIME = 'waiting_schedule_datetime'
    WAITING_SCHEDULE_REASON = 'waiting_schedule_reason'
    
    # Управление
    WAITING_BAN_PLAYER = 'waiting_ban_player'
    WAITING_BAN_REASON = 'waiting_ban_reason'
    WAITING_UNBAN_PLAYER = 'waiting_unban_player'
    WAITING_DELETE_PLAYER = 'waiting_delete_player'
    WAITING_FIND_PLAYER = 'waiting_find_player'
    
    # Рассылка
    WAITING_BROADCAST_MESSAGE = 'waiting_broadcast_message'
    WAITING_GIFT_ALL_AMOUNT = 'waiting_gift_all_amount'
    
    # Фильтр истории
    WAITING_HISTORY_FILTER = 'waiting_history_filter'


def set_state(vk_id, state, **data):
    """Установить состояние пользователя"""
    user_states[vk_id] = {
        'state': state,
        'data': data,
        'timestamp': datetime.now()
    }


def get_state(vk_id):
    """Получить текущее состояние пользователя"""
    if vk_id in user_states:
        state_info = user_states[vk_id]
        
        # Проверка таймаута (5 минут)
        if datetime.now() - state_info['timestamp'] > timedelta(minutes=config.CONFIRMATION_TIMEOUT_MINUTES):
            clear_state(vk_id)
            return State.IDLE, {}
        
        return state_info['state'], state_info.get('data', {})
    
    return State.IDLE, {}


def get_state_data(vk_id, key, default=None):
    """Получить данные из состояния"""
    _, data = get_state(vk_id)
    return data.get(key, default)


def update_state_data(vk_id, **new_data):
    """Обновить данные состояния"""
    if vk_id in user_states:
        user_states[vk_id]['data'].update(new_data)
        user_states[vk_id]['timestamp'] = datetime.now()


def clear_state(vk_id):
    """Очистить состояние пользователя"""
    if vk_id in user_states:
        del user_states[vk_id]


def add_pending_confirmation(confirmation_id, vk_id, action_type, **data):
    """Добавить ожидающее подтверждение"""
    pending_confirmations[confirmation_id] = {
        'vk_id': vk_id,
        'action_type': action_type,
        'data': data,
        'timestamp': datetime.now()
    }


def get_pending_confirmation(confirmation_id):
    """Получить ожидающее подтверждение"""
    if confirmation_id in pending_confirmations:
        confirmation = pending_confirmations[confirmation_id]
        
        # Проверка таймаута
        if datetime.now() - confirmation['timestamp'] > timedelta(minutes=config.CONFIRMATION_TIMEOUT_MINUTES):
            del pending_confirmations[confirmation_id]
            return None
        
        return confirmation
    
    return None


def remove_pending_confirmation(confirmation_id):
    """Удалить подтверждение"""
    if confirmation_id in pending_confirmations:
        del pending_confirmations[confirmation_id]


def cleanup_expired_states():
    """Очистка просроченных состояний"""
    now = datetime.now()
    timeout = timedelta(minutes=config.CONFIRMATION_TIMEOUT_MINUTES)
    
    # Очистка состояний
    expired_states = [
        vk_id for vk_id, state_info in user_states.items()
        if now - state_info['timestamp'] > timeout
    ]
    
    for vk_id in expired_states:
        del user_states[vk_id]
    
    # Очистка подтверждений
    expired_confirmations = [
        conf_id for conf_id, conf in pending_confirmations.items()
        if now - conf['timestamp'] > timeout
    ]
    
    for conf_id in expired_confirmations:
        del pending_confirmations[conf_id]
    
    if expired_states or expired_confirmations:
        print(f"🧹 Очищено {len(expired_states)} состояний и {len(expired_confirmations)} подтверждений")