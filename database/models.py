"""
SQLAlchemy модели для базы данных
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import enum

Base = declarative_base()


class TransactionType(enum.Enum):
    """Типы транзакций"""
    TRANSFER = "transfer"           # Перевод между игроками
    PURCHASE = "purchase"           # Покупка способности/предмета
    ADMIN_GIVE = "admin_give"       # Начисление админом
    ADMIN_TAKE = "admin_take"       # Списание админом
    SCHEDULED_GIVE = "scheduled_give"  # Запланированное начисление


class Player(Base):
    """Профиль игрока"""
    __tablename__ = 'players'

    id = Column(Integer, primary_key=True, autoincrement=True)
    vk_id = Column(Integer, unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    balance = Column(Integer, default=100, nullable=False)
    
    # Система уровней
    experience = Column(Integer, default=0, nullable=False)
    level = Column(Integer, default=1, nullable=False)
    messages_count = Column(Integer, default=0, nullable=False)  # Количество сообщений
    
    # Настройки
    notifications_enabled = Column(Boolean, default=True, nullable=False)
    hide_balance = Column(Boolean, default=False, nullable=False)  # Скрытие баланса в топе
    
    # Блокировка
    is_banned = Column(Boolean, default=False, nullable=False)
    ban_reason = Column(Text, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class Transaction(Base):
    """История транзакций"""
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Участники
    from_player_id = Column(Integer, ForeignKey('players.id'), nullable=True)  # NULL для админских начислений
    to_player_id = Column(Integer, ForeignKey('players.id'), nullable=True)    # NULL для списаний админом
    
    # Детали транзакции
    amount = Column(Integer, nullable=False)
    type = Column(Enum(TransactionType), nullable=False)
    reason = Column(Text, nullable=True)  # Причина (для покупок, админских операций)
    
    # Анонимность
    is_anonymous = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class PurchaseRequest(Base):
    """Запросы на покупку способностей/предметов"""
    __tablename__ = 'purchase_requests'

    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    
    # Детали запроса
    item_description = Column(Text, nullable=False)  # Описание от игрока
    price = Column(Integer, nullable=True)  # Цена (устанавливает админ)
    
    # Статус
    status = Column(String(20), default='pending', nullable=False)  # pending, approved, rejected, completed
    admin_response = Column(Text, nullable=True)  # Ответ админа (отклонение/одобрение)
    
    # VK message IDs для связи сообщений
    player_message_id = Column(Integer, nullable=True)
    admin_message_id = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class Achievement(Base):
    """Достижения игроков"""
    __tablename__ = 'achievements'

    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    
    # Тип достижения
    achievement_type = Column(String(50), nullable=False)  # first_purchase, generous, accumulator, activist
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(10), nullable=False)  # Эмодзи
    
    earned_at = Column(DateTime, server_default=func.now(), nullable=False)


class ScheduledPayment(Base):
    """Запланированные начисления"""
    __tablename__ = 'scheduled_payments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    admin_id = Column(Integer, nullable=False)  # VK ID администратора
    
    amount = Column(Integer, nullable=False)
    reason = Column(Text, nullable=True)
    
    scheduled_for = Column(DateTime, nullable=False)  # Когда начислить
    executed = Column(Boolean, default=False, nullable=False)
    executed_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class ItemTemplate(Base):
    """Шаблоны предметов/способностей (для будущего расширения)"""
    __tablename__ = 'item_templates'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False)  # combat, defense, utility, items
    base_price = Column(Integer, nullable=True)  # Базовая цена (может быть NULL)
    icon = Column(String(10), nullable=False)
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)