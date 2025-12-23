"""
Планировщик запланированных начислений
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import pytz

from database.connection import get_session, close_session
from database.queries import (
    get_due_scheduled_payments,
    mark_payment_executed,
    get_player_by_vk_id
)
from database.models import TransactionType
from database.queries import create_transaction
from utils.notifications import notify_scheduled_payment
import config


class SchedulerService:
    """Сервис для обработки запланированных платежей"""
    
    def __init__(self, vk):
        self.vk = vk
        self.scheduler = BackgroundScheduler(timezone=pytz.timezone(config.TIMEZONE))
    
    def start(self):
        """Запуск планировщика"""
        # Проверка каждую минуту
        self.scheduler.add_job(
            self.process_scheduled_payments,
            trigger=IntervalTrigger(minutes=1),
            id='scheduled_payments',
            name='Обработка запланированных платежей',
            replace_existing=True
        )
        
        self.scheduler.start()
        print("✅ Планировщик запущен!")
    
    def stop(self):
        """Остановка планировщика"""
        self.scheduler.shutdown()
        print("⏸️ Планировщик остановлен")
    
    def process_scheduled_payments(self):
        """Обработка всех запланированных платежей"""
        session = get_session()
        
        try:
            # Получение всех просроченных платежей
            due_payments = get_due_scheduled_payments(session)
            
            if not due_payments:
                return
            
            print(f"⏰ Обработка {len(due_payments)} запланированных платежей...")
            
            for payment in due_payments:
                try:
                    # Получение игрока
                    player = get_player_by_vk_id(session, payment.player_id)
                    
                    if not player:
                        print(f"❌ Игрок {payment.player_id} не найден для платежа #{payment.id}")
                        mark_payment_executed(session, payment.id)
                        continue
                    
                    # Начисление чилликов
                    player.balance += payment.amount
                    
                    # Создание транзакции
                    create_transaction(
                        session,
                        from_player_id=None,
                        to_player_id=player.id,
                        amount=payment.amount,
                        transaction_type=TransactionType.SCHEDULED_GIVE,
                        reason=payment.reason
                    )
                    
                    # Отметка выполнения
                    mark_payment_executed(session, payment.id)
                    
                    # Уведомление игрока
                    notify_scheduled_payment(
                        self.vk,
                        session,
                        player.vk_id,
                        payment.amount,
                        payment.reason
                    )
                    
                    print(f"✅ Выполнен платёж #{payment.id}: {payment.amount} чил. → {player.first_name} {player.last_name}")
                
                except Exception as e:
                    print(f"❌ Ошибка при обработке платежа #{payment.id}: {e}")
                    session.rollback()
                    continue
        
        except Exception as e:
            print(f"❌ Ошибка в планировщике: {e}")
        
        finally:
            close_session(session)