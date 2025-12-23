"""
Валидация данных
"""
import re


def validate_amount(amount_str):
    """
    Валидация суммы чилликов
    Возвращает (valid, amount, error_message)
    """
    try:
        amount = int(amount_str)
        
        if amount <= 0:
            return False, 0, "Сумма должна быть положительной"
        
        if amount > 1000000:
            return False, 0, "Сумма слишком большая (макс. 1,000,000)"
        
        return True, amount, None
    
    except ValueError:
        return False, 0, "Неверный формат суммы. Укажите целое число"


def validate_vk_id(vk_id_str):
    """
    Валидация VK ID
    Возвращает (valid, vk_id, error_message)
    """
    # Попытка извлечь ID из разных форматов
    # @id123, id123, https://vk.com/id123, 123
    
    patterns = [
        r'@id(\d+)',           # @id123
        r'id(\d+)',            # id123
        r'vk\.com/id(\d+)',    # vk.com/id123
        r'^(\d+)$'             # просто число
    ]
    
    for pattern in patterns:
        match = re.search(pattern, vk_id_str)
        if match:
            vk_id = int(match.group(1))
            return True, vk_id, None
    
    return False, 0, "Неверный формат VK ID. Используйте: @id123 или id123 или просто число"


def validate_datetime_format(datetime_str):
    """
    Валидация формата даты/времени
    Формат: YYYY-MM-DD HH:MM или DD.MM.YYYY HH:MM
    """
    from datetime import datetime
    
    formats = [
        '%Y-%m-%d %H:%M',
        '%d.%m.%Y %H:%M',
        '%Y-%m-%d',
        '%d.%m.%Y'
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(datetime_str, fmt)
            # Если время не указано, устанавливаем 12:00
            if fmt in ['%Y-%m-%d', '%d.%m.%Y']:
                dt = dt.replace(hour=12, minute=0)
            return True, dt, None
        except ValueError:
            continue
    
    return False, None, "Неверный формат даты. Используйте: ГГГГ-ММ-ДД ЧЧ:ММ или ДД.ММ.ГГГГ ЧЧ:ММ"


def parse_price_from_admin(text):
    """
    Парсинг цены из ответа администратора
    Формат: "Стоимость: 123" или "Цена: 123" или просто "123"
    """
    patterns = [
        r'стоимость:\s*(\d+)',
        r'цена:\s*(\d+)',
        r'^\s*(\d+)\s*$'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            return True, int(match.group(1)), None
    
    return False, 0, "Не удалось распознать цену. Используйте формат: 'Стоимость: 123'"