"""
VK клавиатуры с кнопками
"""
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import json


def get_main_menu_keyboard():
    """Главное меню игрока"""
    keyboard = VkKeyboard(one_time=False)
    
    keyboard.add_button('💰 Баланс', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('📊 Статистика', color=VkKeyboardColor.PRIMARY)
    
    keyboard.add_line()
    keyboard.add_button('➡️ Перевести', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('🛒 Купить', color=VkKeyboardColor.POSITIVE)
    
    keyboard.add_line()
    keyboard.add_button('📜 История', color=VkKeyboardColor.SECONDARY)
    keyboard.add_button('🏆 Топ игроков', color=VkKeyboardColor.SECONDARY)
    
    keyboard.add_line()
    keyboard.add_button('⚙️ Настройки', color=VkKeyboardColor.SECONDARY)
    keyboard.add_button('❓ Помощь', color=VkKeyboardColor.SECONDARY)
    
    return keyboard.get_keyboard()


def get_admin_menu_keyboard():
    """Меню администратора"""
    keyboard = VkKeyboard(one_time=False)
    
    keyboard.add_button('💸 Начислить', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('💳 Списать', color=VkKeyboardColor.NEGATIVE)
    
    keyboard.add_line()
    keyboard.add_button('📊 Статистика', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('🏆 Топ игроков', color=VkKeyboardColor.PRIMARY)
    
    keyboard.add_line()
    keyboard.add_button('🔨 Управление', color=VkKeyboardColor.SECONDARY)
    keyboard.add_button('📢 Рассылка', color=VkKeyboardColor.SECONDARY)
    
    keyboard.add_line()
    keyboard.add_button('🔙 Выход из админки', color=VkKeyboardColor.SECONDARY)
    
    return keyboard.get_keyboard()


def get_confirmation_keyboard(confirm_text="✅ Подтвердить", cancel_text="❌ Отменить"):
    """Клавиатура подтверждения операции"""
    keyboard = VkKeyboard(one_time=True)
    
    keyboard.add_button(confirm_text, color=VkKeyboardColor.POSITIVE)
    keyboard.add_button(cancel_text, color=VkKeyboardColor.NEGATIVE)
    
    return keyboard.get_keyboard()


def get_amount_keyboard():
    """Клавиатура с быстрым выбором суммы"""
    keyboard = VkKeyboard(one_time=True)
    
    keyboard.add_button('10', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('25', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('50', color=VkKeyboardColor.PRIMARY)
    
    keyboard.add_line()
    keyboard.add_button('100', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('250', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('500', color=VkKeyboardColor.PRIMARY)
    
    keyboard.add_line()
    keyboard.add_button('❌ Отменить', color=VkKeyboardColor.NEGATIVE)
    
    return keyboard.get_keyboard()


def get_category_keyboard():
    """Клавиатура выбора категории способности"""
    keyboard = VkKeyboard(one_time=True)
    
    keyboard.add_button('🔥 Боевые', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('🛡️ Защитные', color=VkKeyboardColor.POSITIVE)
    
    keyboard.add_line()
    keyboard.add_button('⚡ Утилити', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('🎒 Предметы', color=VkKeyboardColor.PRIMARY)
    
    keyboard.add_line()
    keyboard.add_button('✏️ Свой запрос', color=VkKeyboardColor.SECONDARY)
    keyboard.add_button('❌ Отменить', color=VkKeyboardColor.NEGATIVE)
    
    return keyboard.get_keyboard()


def get_history_filter_keyboard():
    """Клавиатура фильтров истории"""
    keyboard = VkKeyboard(one_time=True)
    
    keyboard.add_button('➡️ Переводы', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('🛒 Покупки', color=VkKeyboardColor.PRIMARY)
    
    keyboard.add_line()
    keyboard.add_button('👑 Админ', color=VkKeyboardColor.SECONDARY)
    keyboard.add_button('📋 Все', color=VkKeyboardColor.SECONDARY)
    
    keyboard.add_line()
    keyboard.add_button('❌ Отменить', color=VkKeyboardColor.NEGATIVE)
    
    return keyboard.get_keyboard()


def get_settings_keyboard(notifications_on=True):
    """Клавиатура настроек"""
    keyboard = VkKeyboard(one_time=False)
    
    notif_text = '🔔 Выключить уведомления' if notifications_on else '🔕 Включить уведомления'
    keyboard.add_button(notif_text, color=VkKeyboardColor.PRIMARY)
    
    keyboard.add_line()
    keyboard.add_button('👁️ Скрыть баланс в топе', color=VkKeyboardColor.SECONDARY)
    keyboard.add_button('👁️‍🗨️ Показать баланс в топе', color=VkKeyboardColor.SECONDARY)
    
    keyboard.add_line()
    keyboard.add_button('🔙 Назад', color=VkKeyboardColor.NEGATIVE)
    
    return keyboard.get_keyboard()


def get_admin_management_keyboard():
    """Клавиатура управления для админа"""
    keyboard = VkKeyboard(one_time=False)
    
    keyboard.add_button('🚫 Забанить', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_button('✅ Разбанить', color=VkKeyboardColor.POSITIVE)
    
    keyboard.add_line()
    keyboard.add_button('🗑️ Удалить профиль', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_button('🔍 Найти игрока', color=VkKeyboardColor.PRIMARY)
    
    keyboard.add_line()
    keyboard.add_button('⏰ Запланировать', color=VkKeyboardColor.SECONDARY)
    keyboard.add_button('🎁 Начислить всем', color=VkKeyboardColor.SECONDARY)
    
    keyboard.add_line()
    keyboard.add_button('🔙 Назад', color=VkKeyboardColor.NEGATIVE)
    
    return keyboard.get_keyboard()


def remove_keyboard():
    """Убрать клавиатуру"""
    keyboard = VkKeyboard.get_empty_keyboard()
    return keyboard