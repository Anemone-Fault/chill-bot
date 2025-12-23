"""
Подключение к Supabase PostgreSQL
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from database.models import Base
import config

# Создание движка БД
engine = create_engine(
    config.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Проверка соединения перед использованием
    echo=False  # Логирование SQL запросов (False в продакшене)
)

# Создание фабрики сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Thread-safe сессия
Session = scoped_session(SessionLocal)


def init_db():
    """Инициализация базы данных (создание таблиц)"""
    Base.metadata.create_all(bind=engine)
    print("✅ База данных инициализирована!")


def get_session():
    """Получить сессию БД"""
    session = Session()
    try:
        return session
    except Exception as e:
        session.rollback()
        raise e


def close_session(session):
    """Закрыть сессию БД"""
    try:
        session.close()
    except Exception as e:
        print(f"❌ Ошибка при закрытии сессии: {e}")